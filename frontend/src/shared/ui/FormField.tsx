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
      <label htmlFor={htmlFor} className="field-label">
        {label}
      </label>
      {children}
      {error && <p className="field-error">{error}</p>}
    </div>
  );
}

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string };

export function TextField({ label, error, id, className = "", ...props }: TextFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <input id={id} className={`input ${className}`} {...props} />
    </FieldWrapper>
  );
}

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string; children: ReactNode };

export function SelectField({ label, error, id, children, className = "", ...props }: SelectFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <select id={id} className={`input bg-white ${className}`} {...props}>
        {children}
      </select>
    </FieldWrapper>
  );
}

type TextareaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string };

export function TextareaField({ label, error, id, className = "", ...props }: TextareaFieldProps) {
  return (
    <FieldWrapper label={label} htmlFor={id!} error={error}>
      <textarea id={id} className={`input ${className}`} rows={3} {...props} />
    </FieldWrapper>
  );
}
