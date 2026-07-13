import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { ModelGroup } from "@/lib/schemas";

const TIER_HINT: Record<string, string> = {
  cheap: "günstig",
  standard: "ausgewogen",
  premium: "teurer",
  legacy: "Vorgänger",
};

/** Dropdown zur Modellwahl je Funktion (Text/Bild/Audio). */
export function ModelSelect({
  label,
  group,
  value,
  onChange,
}: {
  label: string;
  group: ModelGroup;
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      <Select value={value} onChange={(e) => onChange(e.target.value)}>
        {group.options.map((opt) => (
          <option key={opt.id} value={opt.id}>
            {opt.label}
            {TIER_HINT[opt.tier] ? ` · ${TIER_HINT[opt.tier]}` : ""}
          </option>
        ))}
      </Select>
    </div>
  );
}

export function VoiceSelect({
  voices,
  value,
  onChange,
}: {
  voices: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label>Stimme</Label>
      <Select value={value} onChange={(e) => onChange(e.target.value)}>
        {voices.map((v) => (
          <option key={v} value={v}>
            {v}
          </option>
        ))}
      </Select>
    </div>
  );
}
