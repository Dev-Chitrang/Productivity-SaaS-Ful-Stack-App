import { useState, useEffect, useRef } from "react"
import { Calendar, CheckSquare, Users } from "lucide-react"

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardAction, CardContent } from "@/components/ui/card"
import {
  useReminderSettings,
  useUpdateReminderSettings,
} from "@/features/settings/hooks/useReminderSettings"

const FREQUENCIES = [
  { value: "DAILY", label: "Daily" },
  { value: "WEEKLY", label: "Weekly" },
  { value: "MONTHLY", label: "Monthly" },
]

const MODULES = [
  { key: "calendar", label: "Calendar", icon: Calendar },
  { key: "tasks", label: "Tasks", icon: CheckSquare },
  { key: "meetings", label: "Meetings", icon: Users },
]

const DEFAULT_GLOBAL_TIME = "09:00"
const DEFAULT_FREQUENCY = "DAILY"

const MODULE_DEFAULTS = {
  calendar: { enabled: false, frequency: DEFAULT_FREQUENCY, time: DEFAULT_GLOBAL_TIME },
  tasks: { enabled: false, frequency: DEFAULT_FREQUENCY, time: DEFAULT_GLOBAL_TIME },
  meetings: { enabled: false, frequency: DEFAULT_FREQUENCY, time: DEFAULT_GLOBAL_TIME },
}

function ReminderSettings() {
  const { data, isLoading } = useReminderSettings()
  const updateMutation = useUpdateReminderSettings()

  const [remindersEnabled, setRemindersEnabled] = useState(false)
  const [scheduleAll, setScheduleAll] = useState(true)
  const [globalFrequency, setGlobalFrequency] = useState(DEFAULT_FREQUENCY)
  const [globalTime, setGlobalTime] = useState(DEFAULT_GLOBAL_TIME)
  const [modules, setModules] = useState({ ...MODULE_DEFAULTS })
  const [errors, setErrors] = useState({})
  const defaultsRef = useRef(null)

  useEffect(() => {
    if (!data) return
    defaultsRef.current = {
      reminders_enabled: data.reminders_enabled ?? false,
      schedule_all: data.schedule_all,
      global_frequency: data.global_frequency || DEFAULT_FREQUENCY,
      global_time: data.global_time ? data.global_time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      calendar: {
        enabled: data.calendar_config.enabled,
        frequency: data.calendar_config.frequency,
        time: data.calendar_config.time ? data.calendar_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
      tasks: {
        enabled: data.tasks_config.enabled,
        frequency: data.tasks_config.frequency,
        time: data.tasks_config.time ? data.tasks_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
      meetings: {
        enabled: data.meetings_config.enabled,
        frequency: data.meetings_config.frequency,
        time: data.meetings_config.time ? data.meetings_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
    }
    setRemindersEnabled(data.reminders_enabled ?? false)
    setScheduleAll(data.schedule_all)
    setGlobalFrequency(data.global_frequency || DEFAULT_FREQUENCY)
    setGlobalTime(data.global_time ? data.global_time.slice(0, 5) : DEFAULT_GLOBAL_TIME)
    setModules({
      calendar: {
        enabled: data.calendar_config.enabled,
        frequency: data.calendar_config.frequency,
        time: data.calendar_config.time ? data.calendar_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
      tasks: {
        enabled: data.tasks_config.enabled,
        frequency: data.tasks_config.frequency,
        time: data.tasks_config.time ? data.tasks_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
      meetings: {
        enabled: data.meetings_config.enabled,
        frequency: data.meetings_config.frequency,
        time: data.meetings_config.time ? data.meetings_config.time.slice(0, 5) : DEFAULT_GLOBAL_TIME,
      },
    })
  }, [data])

  const defaults = defaultsRef.current

  function hasChanges() {
    if (!defaults) return false
    if (remindersEnabled !== defaults.reminders_enabled) return true
    if (!remindersEnabled) return false
    if (scheduleAll !== defaults.schedule_all) return true
    if (scheduleAll) {
      if (globalFrequency !== defaults.global_frequency) return true
      if (globalTime !== defaults.global_time) return true
    } else {
      for (const { key } of MODULES) {
        const mod = modules[key]
        const def = defaults[key]
        if (mod.enabled !== def.enabled) return true
        if (mod.enabled) {
          if (mod.frequency !== def.frequency) return true
          if (mod.time !== def.time) return true
        }
      }
    }
    return false
  }

  function validate() {
    const errs = {}
    if (!remindersEnabled) {
      setErrors(errs)
      return true
    }
    if (scheduleAll) {
      if (!globalFrequency) errs.globalFrequency = "Frequency is required"
      if (!globalTime) errs.globalTime = "Time is required"
    } else {
      for (const { key } of MODULES) {
        const mod = modules[key]
        if (mod.enabled) {
          if (!mod.frequency) errs[`${key}_frequency`] = "Frequency is required"
          if (!mod.time) errs[`${key}_time`] = "Time is required"
        }
      }
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSave() {
    if (!validate()) return

    const config = (mod) => ({
      enabled: mod.enabled,
      frequency: mod.frequency,
      time: `${mod.time}:00`,
    })

    const payload = {
      reminders_enabled: remindersEnabled,
      schedule_all: scheduleAll,
      ...(remindersEnabled && scheduleAll
        ? {
            global_frequency: globalFrequency,
            global_time: `${globalTime}:00`,
          }
        : {
            global_frequency: null,
            global_time: null,
          }),
      calendar_config: config(modules.calendar),
      tasks_config: config(modules.tasks),
      meetings_config: config(modules.meetings),
    }

    updateMutation.mutate(payload)
  }

  function updateModule(key, field, value) {
    setModules((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }))
  }

  if (isLoading) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-semibold tracking-tight">Reminder Engine</h2>
        <div className="space-y-3">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-6 w-32" />
        </div>
      </section>
    )
  }

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold tracking-tight">Reminder Engine</h2>

      <div className="flex items-center justify-between rounded border border-border bg-card px-4 py-3">
        <div className="space-y-0.5">
          <Label className="text-sm font-medium">Enable Reminders</Label>
          <p className="text-xs text-muted-foreground">
            Turn on automated reminder scheduling for your modules.
          </p>
        </div>
        <Switch
          checked={remindersEnabled}
          onCheckedChange={setRemindersEnabled}
        />
      </div>

      {remindersEnabled && (
        <>
          <div className="mt-4">
            <RadioGroup
              value={scheduleAll ? "schedule_all" : "individual"}
              onValueChange={(v) => setScheduleAll(v === "schedule_all")}
              className="mb-3"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem value="schedule_all" id="schedule_all" />
                <Label htmlFor="schedule_all">Schedule all reminders</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="individual" id="individual" />
                <Label htmlFor="individual">Configure individually</Label>
              </div>
            </RadioGroup>

            <p className="mb-4 text-xs text-muted-foreground">
              {scheduleAll
                ? "Use one reminder schedule for Calendar, Tasks, and Meetings."
                : "Set reminders for each module independently."}
            </p>
          </div>

          {scheduleAll ? (
            <div className="space-y-3">
              <div>
                <Label>Frequency</Label>
                <Select value={globalFrequency} onValueChange={setGlobalFrequency}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FREQUENCIES.map((f) => (
                      <SelectItem key={f.value} value={f.value}>
                        {f.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.globalFrequency && (
                  <p className="mt-1 text-xs font-medium text-destructive">{errors.globalFrequency}</p>
                )}
              </div>
              <div>
                <Label>Time</Label>
                <Input
                  type="time"
                  value={globalTime}
                  onChange={(e) => setGlobalTime(e.target.value)}
                  className="mt-1.5"
                />
                {errors.globalTime && (
                  <p className="mt-1 text-xs font-medium text-destructive">{errors.globalTime}</p>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {MODULES.map(({ key, label, icon: Icon }) => {
                const mod = modules[key]
                return (
                  <Card key={key} size="sm">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <Icon className="size-4 text-muted-foreground" />
                        <CardTitle>{label}</CardTitle>
                      </div>
                      <CardAction>
                        <Switch
                          checked={mod.enabled}
                          onCheckedChange={(checked) => updateModule(key, "enabled", checked)}
                        />
                      </CardAction>
                    </CardHeader>
                    {mod.enabled && (
                      <CardContent className="space-y-3">
                        <div>
                          <Label>Frequency</Label>
                          <Select
                            value={mod.frequency}
                            onValueChange={(v) => updateModule(key, "frequency", v)}
                          >
                            <SelectTrigger className="mt-1.5">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {FREQUENCIES.map((f) => (
                                <SelectItem key={f.value} value={f.value}>
                                  {f.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {errors[`${key}_frequency`] && (
                            <p className="mt-1 text-xs font-medium text-destructive">
                              {errors[`${key}_frequency`]}
                            </p>
                          )}
                        </div>
                        <div>
                          <Label>Time</Label>
                          <Input
                            type="time"
                            value={mod.time}
                            onChange={(e) => updateModule(key, "time", e.target.value)}
                            className="mt-1.5"
                          />
                          {errors[`${key}_time`] && (
                            <p className="mt-1 text-xs font-medium text-destructive">
                              {errors[`${key}_time`]}
                            </p>
                          )}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                )
              })}
            </div>
          )}
        </>
      )}

      {!remindersEnabled && (
        <p className="mt-4 text-xs text-muted-foreground">
          Reminder scheduling is currently disabled. Turn it on to configure schedules for Calendar, Tasks, and Meetings.
        </p>
      )}

      <Button
        size="sm"
        className="mt-4"
        onClick={handleSave}
        disabled={updateMutation.isPending || !hasChanges()}
      >
        {updateMutation.isPending ? "Saving..." : "Save reminder settings"}
      </Button>
    </section>
  )
}

export default ReminderSettings
