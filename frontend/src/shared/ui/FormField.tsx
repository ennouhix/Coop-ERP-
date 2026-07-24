import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

interface FieldWrapperProps {
  label: string;
  htmlFor: string;
  error?: string;
  children: ReactNode;
}

function FieldWrapper({ label, htmlFor, error, children }: FieldWrapperProps) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-start text-sm font-medium text-ink-800">
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-start text-xs text-terracotta-600">{error}</p>}
    </div>
  );
}

const inputClasses =
  "w-full rounded-md border border-ink-900/15 px-3 py-2 text-start text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string };

export function TextField({ label, error, id, className = "", ...props }: TextFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <input id={id} className={`${inputClasses} ${className}`} {...props} />
    </FieldWrapper>
  );
}

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string; children: ReactNode };

export function SelectField({ label, error, id, children, className = "", ...props }: SelectFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <select id={id} className={`${inputClasses} bg-white ${className}`} {...props}>
        {children}
      </select>
    </FieldWrapper>
  );
}

type TextareaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string };

export function TextareaField({ label, error, id, className = "", ...props }: TextareaFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <textarea id={id} className={`${inputClasses} ${className}`} rows={3} {...props} />
    </FieldWrapper>
  );
}
