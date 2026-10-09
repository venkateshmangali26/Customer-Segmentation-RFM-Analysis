// Indian Rupee (INR) Currency and Number formatting utilities

export const LAKH = 100_000;
export const CRORE = 10_000_000;

/**
 * Format a number into Indian Rupee notation.
 * Compact format uses Cr (Crores) and L (Lakhs).
 *
 * Example:
 *   formatInr(15000000) => "₹1.50 Cr"
 *   formatInr(2500000)  => "₹25.0 L"
 *   formatInr(12500)    => "₹12.5K" or "₹12,500"
 *   formatInr(850)      => "₹850"
 */
export function formatInr(amount: number, compact: boolean = true): string {
  const abs = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";

  if (compact) {
    if (abs >= CRORE) {
      return `${sign}₹${(abs / CRORE).toFixed(2)} Cr`;
    }
    if (abs >= LAKH) {
      return `${sign}₹${(abs / LAKH).toFixed(2)} L`;
    }
    if (abs >= 10_000) {
      return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
    }
    return `${sign}₹${abs.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  }

  return `${sign}₹${abs.toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Formats monetary amounts for tables where exact values with Indian commas are desired.
 * Example: 145000.5 => "₹1,45,000.50"
 */
export function formatInrExact(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  const abs = Math.abs(amount);
  return `${sign}₹${abs.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}
