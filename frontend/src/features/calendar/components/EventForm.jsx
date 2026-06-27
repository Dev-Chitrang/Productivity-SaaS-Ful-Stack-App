/**
 * EventForm.jsx
 *
 * Create / Edit form for a calendar event.
 * All field names match the Zod schema in schemas/eventSchema.js.
 * Serialization to backend payload is handled by calendarMapper.toCreatePayload().
 */

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { eventSchema, EVENT_TYPE_OPTIONS, EVENT_COLOR_OPTIONS, RECURRENCE_FREQUENCY_OPTIONS } from "../schemas/eventSchema"
import { EVENT_TYPE_LABELS, EVENT_COLOR_LABELS, RECURRENCE_LABELS, EVENT_COLOR_HEX } from "../api/calendarTypes"
import { hhmmToAmpm, ampmToHHmm } from "../api/calendarMapper"

const HOURS_12 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
const MINUTES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
const AMPM_OPTS = ["AM", "PM"]

const COMMON_TIMEZONES = [
    "UTC",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Sao_Paulo", "Europe/London", "Europe/Paris", "Europe/Berlin",
    "Africa/Cairo", "Asia/Dubai", "Asia/Kolkata", "Asia/Singapore",
    "Asia/Tokyo", "Australia/Sydney",
]

/**
 * 12-hour time picker component.
 * Stores value internally as "HH:mm" and converts via mapper helpers.
 */
function TimePicker({ value, onChange, label, id, hasError }) {
    const { hour, minute, ampm } = hhmmToAmpm(value || "09:00")

    const update = (newHour, newMinute, newAmpm) => {
        onChange(ampmToHHmm(newHour, newMinute, newAmpm))
    }

    const selectClass = hasError
        ? "h-8 w-14 border border-destructive bg-background px-1.5 text-xs outline-none focus-visible:border-destructive"
        : "h-8 w-14 border border-input bg-background px-1.5 text-xs outline-none focus-visible:border-ring"

    const selectAmPmClass = hasError
        ? "h-8 w-16 border border-destructive bg-background px-1.5 text-xs outline-none focus-visible:border-destructive"
        : "h-8 w-16 border border-input bg-background px-1.5 text-xs outline-none focus-visible:border-ring"

    return (
        <div>
            {label && (
                <label htmlFor={id} className={cn("text-xs font-medium mb-1 block", hasError && "text-destructive")}>
                    {label}
                </label>
            )}
            <div className="flex items-center gap-1">
                {/* Hour */}
                <select
                    id={id}
                    value={hour}
                    onChange={(e) => update(e.target.value, minute, ampm)}
                    className={selectClass}
                    aria-label="Hour"
                >
                    {HOURS_12.map((h) => (
                        <option key={h} value={h}>{h}</option>
                    ))}
                </select>

                <span className="text-xs text-muted-foreground">:</span>

                {/* Minute */}
                <select
                    value={minute}
                    onChange={(e) => update(hour, e.target.value, ampm)}
                    className={selectClass}
                    aria-label="Minute"
                >
                    {MINUTES.map((m) => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>

                {/* AM/PM */}
                <select
                    value={ampm}
                    onChange={(e) => update(hour, minute, e.target.value)}
                    className={selectAmPmClass}
                    aria-label="AM or PM"
                >
                    {AMPM_OPTS.map((a) => (
                        <option key={a} value={a}>{a}</option>
                    ))}
                </select>
            </div>
        </div>
    )
}

/**
 * @param {Object} props
 * @param {object} props.defaultValues  - from buildCreateDefaults or buildEditDefaults
 * @param {(values: object) => void} props.onSubmit
 * @param {boolean} [props.isPending]
 * @param {"create"|"edit"} [props.mode]
 */
export function EventForm({ defaultValues, onSubmit, isPending = false, mode = "create" }) {
    const form = useForm({
        resolver: zodResolver(eventSchema),
        defaultValues,
    })

    const isAllDay = form.watch("is_all_day")
    const isRecurring = form.watch("is_recurring")

    return (
        <Form {...form}>
            <form
                id="event-form"
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-3 overflow-y-auto max-h-[62vh] pr-1"
            >
                {/* Title */}
                <FormField control={form.control} name="title" render={({ field }) => (
                    <FormItem>
                        <FormLabel>Title <span className="text-destructive">*</span></FormLabel>
                        <FormControl>
                            <Input placeholder="Event title" className="h-8" autoFocus {...field} />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                )} />

                {/* Description */}
                <FormField control={form.control} name="description" render={({ field, fieldState }) => (
                    <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                            <textarea
                                placeholder="Optional description"
                                rows={2}
                                className={cn(
                                    "w-full border bg-background px-2.5 py-1.5 text-xs",
                                    "resize-none outline-none focus-visible:ring-1 focus-visible:ring-ring/50",
                                    "placeholder:text-muted-foreground",
                                    fieldState.error
                                        ? "border-destructive focus-visible:border-destructive"
                                        : "border-input focus-visible:border-ring",
                                )}
                                {...field}
                            />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                )} />

                {/* Event Type + Color */}
                <div className="grid grid-cols-2 gap-3">
                    <FormField control={form.control} name="event_type" render={({ field }) => (
                        <FormItem>
                            <FormLabel>Type</FormLabel>
                            <FormControl>
                                <select
                                    className="h-8 w-full border border-input bg-background px-2 text-xs outline-none focus-visible:border-ring"
                                    {...field}
                                >
                                    {EVENT_TYPE_OPTIONS.map((t) => (
                                        <option key={t} value={t}>{EVENT_TYPE_LABELS[t] ?? t}</option>
                                    ))}
                                </select>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )} />

                    <FormField control={form.control} name="color" render={({ field }) => (
                        <FormItem>
                            <FormLabel>Color</FormLabel>
                            <FormControl>
                                <div className="flex flex-wrap gap-1.5 pt-1">
                                    {EVENT_COLOR_OPTIONS.map((c) => (
                                        <button
                                            key={c}
                                            type="button"
                                            aria-label={`Color: ${EVENT_COLOR_LABELS[c] ?? c}`}
                                            onClick={() => field.onChange(c)}
                                            className={cn(
                                                "size-5 rounded-full transition-transform",
                                                field.value === c
                                                    ? "ring-2 ring-offset-1 ring-foreground scale-110"
                                                    : "hover:scale-110",
                                            )}
                                            style={{ backgroundColor: EVENT_COLOR_HEX[c] }}
                                        />
                                    ))}
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )} />
                </div>

                {/* All-day toggle */}
                <FormField control={form.control} name="is_all_day" render={({ field }) => (
                    <FormItem>
                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="is_all_day"
                                checked={field.value}
                                onChange={(e) => field.onChange(e.target.checked)}
                                className="size-3.5 accent-primary"
                            />
                            <FormLabel htmlFor="is_all_day" className="cursor-pointer text-xs font-normal">
                                All-day event
                            </FormLabel>
                        </div>
                    </FormItem>
                )} />

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                    <FormField control={form.control} name="start_date" render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>Start date <span className="text-destructive">*</span></FormLabel>
                            <FormControl>
                                <input
                                    type="date"
                                    className={cn(
                                        "h-8 w-full border bg-background px-2 text-xs outline-none",
                                        fieldState.error
                                            ? "border-destructive focus-visible:border-destructive"
                                            : "border-input focus-visible:border-ring",
                                    )}
                                    {...field}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )} />
                    <FormField control={form.control} name="end_date" render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>End date <span className="text-destructive">*</span></FormLabel>
                            <FormControl>
                                <input
                                    type="date"
                                    className={cn(
                                        "h-8 w-full border bg-background px-2 text-xs outline-none",
                                        fieldState.error
                                            ? "border-destructive focus-visible:border-destructive"
                                            : "border-input focus-visible:border-ring",
                                    )}
                                    {...field}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )} />
                </div>

                {/* 12-hour time pickers — hidden when all-day */}
                {!isAllDay && (
                    <div className="grid grid-cols-2 gap-3">
                        <FormField control={form.control} name="start_hhmm" render={({ field, fieldState }) => (
                            <FormItem>
                                <FormControl>
                                    <TimePicker
                                        id="start_time_picker"
                                        label="Start time"
                                        value={field.value}
                                        onChange={field.onChange}
                                        hasError={!!fieldState.error}
                                    />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )} />
                        <FormField control={form.control} name="end_hhmm" render={({ field, fieldState }) => (
                            <FormItem>
                                <FormControl>
                                    <TimePicker
                                        id="end_time_picker"
                                        label="End time"
                                        value={field.value}
                                        onChange={field.onChange}
                                        hasError={!!fieldState.error}
                                    />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )} />
                    </div>
                )}

                {/* Timezone */}
                <FormField control={form.control} name="timezone" render={({ field }) => (
                    <FormItem>
                        <FormLabel>Timezone</FormLabel>
                        <FormControl>
                            <select
                                className="h-8 w-full border border-input bg-background px-2 text-xs outline-none focus-visible:border-ring"
                                {...field}
                            >
                                {COMMON_TIMEZONES.map((tz) => (
                                    <option key={tz} value={tz}>{tz}</option>
                                ))}
                            </select>
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                )} />

                {/* Location */}
                <FormField control={form.control} name="location" render={({ field }) => (
                    <FormItem>
                        <FormLabel>Location</FormLabel>
                        <FormControl>
                            <Input placeholder="Optional location" className="h-8" {...field} />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                )} />

                {/* Recurring toggle */}
                <FormField control={form.control} name="is_recurring" render={({ field }) => (
                    <FormItem>
                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="is_recurring"
                                checked={field.value}
                                onChange={(e) => field.onChange(e.target.checked)}
                                className="size-3.5 accent-primary"
                            />
                            <FormLabel htmlFor="is_recurring" className="cursor-pointer text-xs font-normal">
                                Recurring event
                            </FormLabel>
                        </div>
                    </FormItem>
                )} />

                {/* Recurrence options */}
                {isRecurring && (
                    <div className="space-y-3 border border-border p-3 bg-muted/30">
                        <div className="grid grid-cols-2 gap-3">
                            <FormField control={form.control} name="recurrence_frequency" render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Frequency</FormLabel>
                                    <FormControl>
                                        <select
                                            className="h-8 w-full border border-input bg-background px-2 text-xs outline-none focus-visible:border-ring"
                                            {...field}
                                        >
                                            {RECURRENCE_FREQUENCY_OPTIONS.map((f) => (
                                                <option key={f} value={f}>{RECURRENCE_LABELS[f] ?? f}</option>
                                            ))}
                                        </select>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )} />
                            <FormField control={form.control} name="recurrence_interval" render={({ field, fieldState }) => (
                                <FormItem>
                                    <FormLabel>Every (interval)</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="number"
                                            min={1}
                                            max={99}
                                            className={cn("h-8", fieldState.error && "border-destructive focus-visible:border-destructive")}
                                            {...field}
                                            onChange={(e) => field.onChange(Number(e.target.value))}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )} />
                        </div>
                        <FormField control={form.control} name="recurrence_end_date" render={({ field, fieldState }) => (
                            <FormItem>
                                <FormLabel>Recurrence end date (optional)</FormLabel>
                                <FormControl>
                                    <input
                                        type="date"
                                        className={cn(
                                            "h-8 w-full border bg-background px-2 text-xs outline-none",
                                            fieldState.error
                                                ? "border-destructive focus-visible:border-destructive"
                                                : "border-input focus-visible:border-ring",
                                        )}
                                        {...field}
                                    />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )} />
                    </div>
                )}
            </form>
        </Form>
    )
}
