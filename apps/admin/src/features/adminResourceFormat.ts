export const emptyToNull = (value?: string | null) => (value && value.trim().length > 0 ? value.trim() : null);
