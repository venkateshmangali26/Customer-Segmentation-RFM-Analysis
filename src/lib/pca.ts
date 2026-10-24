/**
 * Principal Component Analysis (PCA) 2D projection engine.
 * Projects log1p-transformed and standardized Recency, Frequency, and Monetary (RFM)
 * features onto the first 2 principal components for 2D cluster visualization.
 */

export type PcaPoint = {
  pc1: number;
  pc2: number;
};

export type PcaResult = {
  points: PcaPoint[];
  varianceExplained: [number, number]; // e.g. [72.5, 18.3] (percentages)
};

function jacobi3x3(A: number[][]): { eigenvalues: number[]; eigenvectors: number[][] } {
  const V = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
  ];
  const a = A.map((row) => [...row]);

  for (let iter = 0; iter < 50; iter++) {
    let p = 0;
    let q = 1;
    let maxVal = Math.abs(a[0][1]);
    if (Math.abs(a[0][2]) > maxVal) {
      p = 0;
      q = 2;
      maxVal = Math.abs(a[0][2]);
    }
    if (Math.abs(a[1][2]) > maxVal) {
      p = 1;
      q = 2;
      maxVal = Math.abs(a[1][2]);
    }

    if (maxVal < 1e-9) break;

    const diff = a[q][q] - a[p][p];
    const theta = 0.5 * Math.atan2(2 * a[p][q], diff);
    const c = Math.cos(theta);
    const s = Math.sin(theta);

    const app = c * c * a[p][p] - 2 * s * c * a[p][q] + s * s * a[q][q];
    const aqq = s * s * a[p][p] + 2 * s * c * a[p][q] + c * c * a[q][q];
    a[p][q] = 0;
    a[q][p] = 0;
    a[p][p] = app;
    a[q][q] = aqq;

    for (let i = 0; i < 3; i++) {
      if (i !== p && i !== q) {
        const aip = c * a[i][p] - s * a[i][q];
        const aiq = s * a[i][p] + c * a[i][q];
        a[i][p] = aip;
        a[p][i] = aip;
        a[i][q] = aiq;
        a[q][i] = aiq;
      }
      const vip = c * V[i][p] - s * V[i][q];
      const viq = s * V[i][p] + c * V[i][q];
      V[i][p] = vip;
      V[i][q] = viq;
    }
  }

  const eigenvalues = [a[0][0], a[1][1], a[2][2]];
  const indices = [0, 1, 2].sort((i, j) => eigenvalues[j] - eigenvalues[i]);
  const sortedEig = indices.map((i) => Math.max(0, eigenvalues[i]));
  const sortedVec = [
    [V[0][indices[0]], V[0][indices[1]], V[0][indices[2]]],
    [V[1][indices[0]], V[1][indices[1]], V[1][indices[2]]],
    [V[2][indices[0]], V[2][indices[1]], V[2][indices[2]]],
  ];

  return { eigenvalues: sortedEig, eigenvectors: sortedVec };
}

export function computePca2D(
  items: Array<{ recencyDays: number; frequency: number; monetary: number }>
): PcaResult {
  const n = items.length;
  if (n === 0) {
    return { points: [], varianceExplained: [0, 0] };
  }

  if (n < 3) {
    return {
      points: items.map(() => ({ pc1: 0, pc2: 0 })),
      varianceExplained: [50, 50],
    };
  }

  // 1. log1p feature transformation
  const X = items.map((it) => [
    Math.log1p(Math.max(0, it.recencyDays)),
    Math.log1p(Math.max(0, it.frequency)),
    Math.log1p(Math.max(0, it.monetary)),
  ]);

  // 2. Means and Standard Deviations
  const means = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    means[0] += X[i][0];
    means[1] += X[i][1];
    means[2] += X[i][2];
  }
  means[0] /= n;
  means[1] /= n;
  means[2] /= n;

  const stds = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    stds[0] += Math.pow(X[i][0] - means[0], 2);
    stds[1] += Math.pow(X[i][1] - means[1], 2);
    stds[2] += Math.pow(X[i][2] - means[2], 2);
  }
  stds[0] = Math.sqrt(stds[0] / (n - 1)) || 1;
  stds[1] = Math.sqrt(stds[1] / (n - 1)) || 1;
  stds[2] = Math.sqrt(stds[2] / (n - 1)) || 1;

  // 3. Standardization (Z-score)
  const Z = X.map((row) => [
    (row[0] - means[0]) / stds[0],
    (row[1] - means[1]) / stds[1],
    (row[2] - means[2]) / stds[2],
  ]);

  // 4. Covariance Matrix (3x3)
  const cov = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
  ];
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < 3; j++) {
      for (let k = 0; k < 3; k++) {
        cov[j][k] += Z[i][j] * Z[i][k];
      }
    }
  }
  for (let j = 0; j < 3; j++) {
    for (let k = 0; k < 3; k++) {
      cov[j][k] /= n - 1;
    }
  }

  // 5. Eigenvalue decomposition
  const { eigenvalues, eigenvectors } = jacobi3x3(cov);
  const totalVariance = eigenvalues[0] + eigenvalues[1] + eigenvalues[2] || 1;
  const var1 = Number(((eigenvalues[0] / totalVariance) * 100).toFixed(1));
  const var2 = Number(((eigenvalues[1] / totalVariance) * 100).toFixed(1));

  // 6. Project onto PC1 and PC2 (eigenvectors columns 0 and 1)
  const v1 = [eigenvectors[0][0], eigenvectors[1][0], eigenvectors[2][0]];
  const v2 = [eigenvectors[0][1], eigenvectors[1][1], eigenvectors[2][1]];

  const points: PcaPoint[] = Z.map((row) => ({
    pc1: Number((row[0] * v1[0] + row[1] * v1[1] + row[2] * v1[2]).toFixed(2)),
    pc2: Number((row[0] * v2[0] + row[1] * v2[1] + row[2] * v2[2]).toFixed(2)),
  }));

  return {
    points,
    varianceExplained: [var1, var2],
  };
}
