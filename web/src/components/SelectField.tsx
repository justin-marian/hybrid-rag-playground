import { KeyboardEvent, useEffect, useId, useRef, useState } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  ariaLabel?: string;
  placeholder?: string;
}


function CheckIcon() {
  return (
    <svg
      className="select-field__check-icon"
      viewBox="0 0 20 20"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M5 10.5L8.2 13.7L15 6.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SelectField({
  value,
  options,
  onChange,
  disabled = false,
  ariaLabel,
  placeholder = "Select an option",
}: SelectFieldProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const listboxId = useId();

  const selected = options.find((option) => option.value === value);
  const isDisabled = disabled || options.length === 0;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const selectOption = (option: SelectOption) => {
    onChange(option.value);
    setOpen(false);
  };

  const handleButtonKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen(true);
    }
  };

  return (
    <div className="select-field" ref={rootRef}>
      <button
        className={`select-field__button ${open ? "select-field__button--open" : ""}`}
        type="button"
        disabled={isDisabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listboxId : undefined}
        aria-label={ariaLabel}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleButtonKeyDown}
      >
        <span className={!selected ? "select-field__placeholder" : undefined}>
          {selected?.label ?? placeholder}
        </span>
        <span className="select-field__chevron" aria-hidden="true">
          <svg viewBox="0 0 20 20" focusable="false">
            <path d="M5.5 7.5L10 12l4.5-4.5" />
          </svg>
        </span>
      </button>

      {open && !isDisabled && (
        <div className="select-field__menu" id={listboxId} role="listbox" aria-label={ariaLabel}>
          {options.map((option) => {
            const active = option.value === value;

            return (
              <button
                key={option.value}
                className={`select-field__option ${active ? "select-field__option--active" : ""}`}
                type="button"
                role="option"
                aria-selected={active}
                onClick={() => selectOption(option)}
              >
                <span className="select-field__check" aria-hidden="true">
                  {active ? <CheckIcon /> : null}
                </span>
                <span>{option.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
