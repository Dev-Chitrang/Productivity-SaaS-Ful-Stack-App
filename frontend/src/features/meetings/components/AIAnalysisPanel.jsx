import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import {
  useMeetingAnalysis,
  useMeetingAnalysisStatus,
  analysisKeys,
} from "../hooks/useMeetingsApi"
import {
  useAiSuggestions,
  useCreateTaskFromSuggestion,
  useRejectSuggestion,
} from "../hooks/useAiSuggestionsApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Robot,
  Spinner,
  CheckCircle,
  XCircle,
  ArrowClockwise,
  FileText,
  ListChecks,
  Check,
  Prohibit,
} from "@phosphor-icons/react"

function PriorityBadge({ priority }) {
  const colors = {
    HIGH: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
    MEDIUM:
      "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800",
    LOW: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
  }
  const color = colors[priority] || colors.MEDIUM
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${color}`}
    >
      {priority}
    </span>
  )
}

function SuggestionStatusBadge({ status }) {
  if (status === "CREATED") {
    return (
      <span className="inline-flex items-center gap-1 rounded border border-green-200 bg-green-50 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
        <Check className="size-2.5" weight="bold" />
        Created
      </span>
    )
  }
  if (status === "REJECTED") {
    return (
      <span className="inline-flex items-center gap-1 rounded border border-red-200 bg-red-50 px-1.5 py-0.5 text-[10px] font-medium text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
        <Prohibit className="size-2.5" weight="bold" />
        Rejected
      </span>
    )
  }
  return null
}

export function AIAnalysisPanel({ meetingId, enabled }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [pendingSuggestionId, setPendingSuggestionId] = useState(null)
  const {
    data: analysis,
    isLoading: analysisLoading,
    isError,
  } = useMeetingAnalysis(meetingId)
  const { data: statusData } = useMeetingAnalysisStatus(meetingId)

  const analysisId = analysis?.id
  const { data: suggestions = [] } = useAiSuggestions(analysisId)

  const createTaskMutation = useCreateTaskFromSuggestion()
  const rejectMutation = useRejectSuggestion()

  const status = statusData?.status || analysis?.status

  useEffect(() => {
    if (statusData?.status === "COMPLETED" || statusData?.status === "FAILED") {
      queryClient.invalidateQueries({
        queryKey: analysisKeys.analysis(meetingId),
      })
    }
  }, [statusData?.status, meetingId, queryClient])

  const handleRetry = () => {
    queryClient.invalidateQueries({
      queryKey: analysisKeys.analysis(meetingId),
    })
    queryClient.invalidateQueries({
      queryKey: analysisKeys.status(meetingId),
    })
  }

  const handleCreateTask = async (suggestion) => {
    setPendingSuggestionId(suggestion.id)
    try {
      await createTaskMutation.mutateAsync({
        suggestionId: suggestion.id,
        analysisId,
        payload: {},
      })
    } catch {}
    setPendingSuggestionId(null)
  }

  const handleReject = async (suggestion) => {
    setPendingSuggestionId(suggestion.id)
    try {
      await rejectMutation.mutateAsync({
        suggestionId: suggestion.id,
        analysisId,
      })
    } catch {}
    setPendingSuggestionId(null)
  }

  if (!enabled) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted">
              <Robot className="size-5 text-muted-foreground" weight="light" />
            </div>
            <p className="mb-1 text-sm font-medium text-foreground">
              AI analysis not enabled
            </p>
            <p className="max-w-xs text-xs text-muted-foreground">
              AI analysis was not enabled for this meeting.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (status === "PROCESSING" || status === "PENDING") {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Spinner className="size-6 animate-spin text-primary" />
            <p className="mt-3 text-sm text-muted-foreground">
              {status === "PENDING"
                ? "Waiting to process AI analysis..."
                : "Generating AI analysis..."}
            </p>
            <div className="mt-6 w-full max-w-md space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (analysisLoading) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 py-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (statusData === null) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted">
              <FileText className="size-5 text-muted-foreground" weight="light" />
            </div>
            <p className="mb-1 text-sm font-medium text-foreground">
              No Analysis Available
            </p>
            <p className="max-w-xs text-xs text-muted-foreground">
              No AI analysis has been generated for this meeting yet.
              If AI analysis is enabled, it will appear here after the meeting has
              finished and processing is complete.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (status === "FAILED" || isError) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted">
              <XCircle
                className="size-5 text-destructive"
                weight="light"
              />
            </div>
            <p className="mb-1 text-sm font-medium text-foreground">
              Analysis failed
            </p>
            <p className="mb-4 max-w-xs text-xs text-muted-foreground">
              AI analysis could not be generated.
            </p>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              <ArrowClockwise className="size-3.5" />
              Refresh Status
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (analysis && status === "COMPLETED") {
    return (
      <Card className="mt-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>AI Analysis</CardTitle>
            <span className="inline-flex items-center gap-1 rounded border border-green-200 bg-green-50 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
              <CheckCircle className="size-3" weight="fill" />
              Completed
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {analysis.summary && (
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Summary
              </h4>
              <p className="text-sm">{analysis.summary}</p>
            </div>
          )}

          {analysis.agenda_coverage_percentage != null && (
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Agenda Coverage
              </h4>
              <div className="mb-3 flex items-center gap-3">
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{
                      width: `${analysis.agenda_coverage_percentage}%`,
                    }}
                  />
                </div>
                <span className="text-xs font-medium tabular-nums">
                  {analysis.agenda_coverage_percentage}%
                </span>
              </div>
            </div>
          )}

          {analysis.covered_points?.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Covered Points
              </h4>
              <ul className="space-y-1">
                {analysis.covered_points.map((point, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs"
                  >
                    <CheckCircle
                      className="mt-0.5 size-3.5 shrink-0 text-green-500"
                      weight="fill"
                    />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysis.out_of_agenda_points?.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Out of Agenda
              </h4>
              <ul className="space-y-1">
                {analysis.out_of_agenda_points.map((point, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs"
                  >
                    <span className="mt-0.5 flex size-3.5 shrink-0 items-center justify-center text-muted-foreground">
                      &bull;
                    </span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {suggestions.length > 0 && (
            <div>
              <h4 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Suggested Tasks
              </h4>
              <div className="space-y-2">
                {suggestions.map((suggestion) => (
                  <div
                    key={suggestion.id}
                    className="space-y-1.5 rounded border border-border p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-medium">{suggestion.title}</p>
                      <PriorityBadge priority={suggestion.priority} />
                    </div>
                    {suggestion.description && (
                      <p className="text-xs text-muted-foreground">
                        {suggestion.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 pt-1">
                      {suggestion.status === "PENDING" ? (
                        <>
                          <Button
                            variant="default"
                            size="sm"
                            className="h-7 text-[11px]"
                            onClick={() => handleCreateTask(suggestion)}
                            disabled={pendingSuggestionId === suggestion.id}
                          >
                            <ListChecks className="size-3 mr-1" />
                            {pendingSuggestionId === suggestion.id ? "Creating..." : "Create Task"}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-[11px] text-muted-foreground"
                            onClick={() => handleReject(suggestion)}
                            disabled={pendingSuggestionId === suggestion.id}
                          >
                            <Prohibit className="size-3 mr-1" />
                            Reject
                          </Button>
                        </>
                      ) : (
                        <div className="flex items-center gap-2">
                          <SuggestionStatusBadge status={suggestion.status} />
                          {suggestion.status === "CREATED" && suggestion.created_task_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-[11px]"
                              onClick={() => navigate(`/tasks`)}
                            >
                              <ListChecks className="size-3 mr-1" />
                              Open Task
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return null
}
