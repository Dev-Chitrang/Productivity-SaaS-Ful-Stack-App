export const DEFAULT_BOARD_DATA = {
    version: 1,
    elements: [],
}

export const WhiteboardTool = Object.freeze({
    SELECT: "select",
    PEN: "pen",
    RECTANGLE: "rectangle",
    CIRCLE: "circle",
    ARROW: "arrow",
    LINE: "line",
    TEXT: "text",
})

export const WhiteboardFilter = Object.freeze({
    ALL: "all",
    FAVORITE: "favorite",
    ARCHIVED: "archived",
    DELETED: "deleted",
})

export const ELEMENT_TYPES = Object.freeze({
    PEN: "pen",
    RECTANGLE: "rectangle",
    CIRCLE: "circle",
    ARROW: "arrow",
    LINE: "line",
    TEXT: "text",
})
