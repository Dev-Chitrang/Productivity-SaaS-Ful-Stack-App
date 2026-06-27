export function toCreatePayload(formValues) {
    return {
        title: formValues.title || null,
        content: formValues.content || "",
        category: formValues.category || null,
        tags: formValues.tags || [],
        is_pinned: formValues.is_pinned ?? false,
        is_favorite: formValues.is_favorite ?? false,
        is_archived: formValues.is_archived ?? false,
    }
}

export function toUpdatePayload(formValues) {
    const payload = {}
    if (formValues.title !== undefined) payload.title = formValues.title || null
    if (formValues.content !== undefined) payload.content = formValues.content
    if (formValues.category !== undefined) payload.category = formValues.category || null
    if (formValues.tags !== undefined) payload.tags = formValues.tags
    return payload
}
