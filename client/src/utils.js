// Check if value is a plain object such as {}
export const isPlainObject = (val) => {
  if (val === undefined || val === null || val.then) return false;
  return Object.prototype.toString.call(val) === "[object Object]";
};
