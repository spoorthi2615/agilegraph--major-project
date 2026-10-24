export function escapeCsvValue(val: any): string {
  if (val === null || val === undefined) {
    return '""';
  }
  let str = String(val);
  
  // Neutralize formula injection in spreadsheet applications (=, +, -, @, \t, \r, %, |)
  // Check if raw string starts with formula chars or whitespace followed by formula chars
  // Note: we test raw string first to catch leading \t, \r, etc. before trim removes them.
  if (/^[=+\-@\t\r%|]/.test(str) || /^\s+[=+\-@%|]/.test(str)) {
    str = `'${str}`;
  }
  
  // Escape quotes by doubling them
  str = str.replace(/"/g, '""');
  return `"${str}"`;
}
