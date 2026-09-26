"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { FileText, UploadCloud, X, AlertCircle } from "lucide-react";

export interface FileUploadProps {
  value?: File | null;
  onChange: (file: File | null) => void;
  onError?: (error: string | null) => void;
  accept?: string;
  maxSizeMB?: number;
  disabled?: boolean;
  className?: string;
}

export function FileUpload({
  value,
  onChange,
  onError,
  accept = ".pdf,application/pdf",
  maxSizeMB = 20,
  disabled = false,
  className,
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const setError = (msg: string | null) => {
    setErrorMessage(msg);
    if (onError) {
      onError(msg);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);
    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setError("Invalid file type: Only PDF documents (.pdf) are accepted for legal analysis.");
      return;
    }

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File size exceeds limit: Maximum allowed size is ${maxSizeMB}MB.`);
      return;
    }

    onChange(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      validateAndSetFile(selectedFile);
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (inputRef.current) {
      inputRef.current.value = "";
    }
    setError(null);
    onChange(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className={cn("w-full space-y-2", className)}>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        disabled={disabled}
        className="hidden"
      />

      {!value ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          className={cn(
            "flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-surface-raised/50 p-6 text-center transition-all cursor-pointer hover:border-accent hover:bg-surface-raised",
            isDragOver && "border-accent bg-surface-raised ring-2 ring-accent/20",
            disabled && "cursor-not-allowed opacity-50 hover:border-border hover:bg-surface-raised/50"
          )}
        >
          <div className="rounded-full bg-surface p-3 text-muted mb-2">
            <UploadCloud className="h-6 w-6 text-accent" />
          </div>
          <p className="text-sm font-medium text-foreground">
            Click to upload or drag and drop Privacy Policy / DPA PDF
          </p>
          <p className="text-xs text-muted mt-1">
            PDF files only (max {maxSizeMB}MB) • Processed transiently in-memory
          </p>
        </div>
      ) : (
        <div className="flex items-center justify-between rounded-lg border border-border bg-surface-raised p-3.5">
          <div className="flex items-center gap-3 min-w-0">
            <div className="rounded-md bg-accent/10 p-2 text-accent">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground truncate">
                {value.name}
              </p>
              <p className="text-xs text-muted">
                {formatFileSize(value.size)} • PDF Ready for Ingestion
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            disabled={disabled}
            className="rounded p-1 text-muted hover:bg-surface hover:text-foreground transition-colors"
            title="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-center gap-1.5 text-xs text-red-400">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
