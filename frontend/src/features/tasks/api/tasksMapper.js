export function toCreatePayload(formValues) {
    return {
        title: formValues.title || "Untitled",
        description: formValues.description || null,
        status: formValues.status || "TODO",
        priority: formValues.priority || "MEDIUM",
        due_date: formValues.due_date || null,
        labels: formValues.labels || [],
        checklist: formValues.checklist || [],
        is_pinned: formValues.is_pinned ?? false,
        is_favorite: formValues.is_favorite ?? false,
        is_archived: formValues.is_archived ?? false,
    }
}

export function toUpdatePayload(formValues) {
    const payload = {}
    if (formValues.title !== undefined) payload.title = formValues.title
    if (formValues.description !== undefined) payload.description = formValues.description
    if (formValues.status !== undefined) payload.status = formValues.status
    if (formValues.priority !== undefined) payload.priority = formValues.priority
    if (formValues.due_date !== undefined) payload.due_date = formValues.due_date
    if (formValues.labels !== undefined) payload.labels = formValues.labels
    if (formValues.checklist !== undefined) payload.checklist = formValues.checklist
    return payload
}
