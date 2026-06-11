"use client";

import * as React from "react";
import { Paintbrush } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  label?: string;
  className?: string;
}

export function ColorPicker({ value, onChange, label, className }: ColorPickerProps) {
  const [internalValue, setInternalValue] = React.useState(value);

  React.useEffect(() => {
    setInternalValue(value);
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);

    // Validar se é um hex válido antes de propagar
    if (/^#[0-9A-Fa-f]{6}$/.test(newValue)) {
      onChange(newValue);
    }
  };

  const handleColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    onChange(newValue);
  };

  // Cores predefinidas populares
  const presetColors = [
    "#3b82f6", // blue-500
    "#8b5cf6", // violet-500
    "#10b981", // green-500
    "#f59e0b", // amber-500
    "#ef4444", // red-500
    "#ec4899", // pink-500
    "#06b6d4", // cyan-500
    "#6366f1", // indigo-500
    "#14b8a6", // teal-500
    "#f97316", // orange-500
    "#84cc16", // lime-500
    "#a855f7", // purple-500
  ];

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {label && <Label>{label}</Label>}
      <div className="flex gap-2">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-[220px] justify-start text-left font-normal"
            >
              <div className="w-full flex items-center gap-2">
                <div
                  className="h-4 w-4 rounded border"
                  style={{ backgroundColor: internalValue }}
                />
                <span className="flex-1 text-sm">{internalValue}</span>
                <Paintbrush className="ml-auto h-4 w-4" />
              </div>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64" align="start">
            <div className="flex flex-col gap-4">
              {/* Seletor nativo de cor */}
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={internalValue}
                  onChange={handleColorChange}
                  className="h-10 w-full cursor-pointer rounded border"
                />
              </div>

              {/* Cores predefinidas */}
              <div className="grid grid-cols-6 gap-2">
                {presetColors.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className={cn(
                      "h-8 w-8 rounded border-2 transition-all hover:scale-110",
                      internalValue === color ? "border-foreground" : "border-transparent"
                    )}
                    style={{ backgroundColor: color }}
                    onClick={() => {
                      setInternalValue(color);
                      onChange(color);
                    }}
                  />
                ))}
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Input manual para código hex */}
        <Input
          type="text"
          value={internalValue}
          onChange={handleInputChange}
          placeholder="#000000"
          className="w-[120px] font-mono text-sm"
          maxLength={7}
        />
      </div>
    </div>
  );
}
