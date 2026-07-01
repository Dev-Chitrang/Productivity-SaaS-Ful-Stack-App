export function toCreatePayload(formValues) {
    return {
        title: formValues.title || "Untitled",
        board_data: formValues.board_data || { version: 1, elements: [] },
    }
}

export function toUpdatePayload(formValues) {
    const payload = {}
    if (formValues.title !== undefined) payload.title = formValues.title
    return payload
}

export function toAutosavePayload(boardData) {
    return { board_data: boardData }
}
