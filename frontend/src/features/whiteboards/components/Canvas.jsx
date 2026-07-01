import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { Stage, Layer, Rect, Circle, Line, Arrow, Text, Transformer } from "react-konva"
import { WhiteboardTool, ELEMENT_TYPES } from "../api/whiteboardsTypes"
import { generateElementId } from "../utils/whiteboardUtils"
import { useThemeContext } from "@/context/ThemeContext"

const MIN_SHAPE_SIZE = 5

function CanvasTextInput({ x, y, text, fontSize, fontFamily, fill, onSubmit, onCancel, onTextChange }) {
    const [value, setValue] = useState(text || "")
    const inputRef = useRef(null)

    useEffect(() => {
        const timer = setTimeout(() => inputRef.current?.focus(), 0)
        return () => clearTimeout(timer)
    }, [])

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            onSubmit(value)
        }
        if (e.key === "Escape") {
            onCancel()
        }
    }

    return (
        <div
            style={{
                position: "absolute",
                left: x,
                top: y,
                transform: "translate(-50%, -50%)",
                zIndex: 1000,
            }}
        >
            <input
                ref={inputRef}
                type="text"
                value={value}
                onChange={(e) => {
                    setValue(e.target.value)
                    onTextChange?.(e.target.value)
                }}
                onKeyDown={handleKeyDown}
                style={{
                    fontSize: `${fontSize || 18}px`,
                    fontFamily: fontFamily || "sans-serif",
                    color: fill || "#000000",
                    background: "transparent",
                    border: "none",
                    outline: "1px dashed #3b82f6",
                    padding: "2px 4px",
                    minWidth: "60px",
                }}
            />
        </div>
    )
}

export function WhiteboardCanvas({
    elements,
    selectedId,
    tool,
    strokeColor,
    strokeWidth,
    zoom,
    onElementsChange,
    onSelectElement,
    onStageRef,
    onZoomChange,
}) {
    const stageRef = useRef(null)
    const transformerRef = useRef(null)
    const shapeRefs = useRef({})
    const containerRef = useRef(null)
    const [stageSize, setStageSize] = useState({ width: 800, height: 600 })
    const [isDrawing, setIsDrawing] = useState(false)
    const [drawingElement, setDrawingElement] = useState(null)
    const [editingText, setEditingText] = useState(null)
    const editingTextRef = useRef(null)
    editingTextRef.current = editingText
    const { theme } = useThemeContext()

    const stageBg = theme === "dark" ? "#1e1e2e" : "#ffffff"

    useEffect(() => {
        const container = containerRef.current
        if (!container) return
        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect
                setStageSize({ width: Math.floor(width), height: Math.floor(height) })
            }
        })
        observer.observe(container)
        return () => observer.disconnect()
    }, [])

    useEffect(() => {
        onStageRef?.(stageRef.current)
    }, [onStageRef])

    useEffect(() => {
        if (stageRef.current) {
            const container = stageRef.current.container()
            if (container) container.tabIndex = -1
        }
    }, [])

    useEffect(() => {
        if (selectedId && transformerRef.current) {
            const node = shapeRefs.current[selectedId]
            if (node) {
                transformerRef.current.nodes([node])
                transformerRef.current.getLayer()?.batchDraw()
                return
            }
        }
        transformerRef.current?.nodes([])
        transformerRef.current?.getLayer()?.batchDraw()
    }, [selectedId, elements])

    const commitEditingText = useCallback(() => {
        const current = editingTextRef.current
        if (!current) return
        const trimmed = (current.text || "").trim()
        if (trimmed) {
            const existing = elements.find((el) => el.id === current.id)
            if (existing) {
                onElementsChange(
                    elements.map((el) =>
                        el.id === current.id ? { ...el, text: trimmed } : el,
                    ),
                )
            } else {
                onElementsChange([
                    ...elements,
                    {
                        id: current.id,
                        type: ELEMENT_TYPES.TEXT,
                        x: current.x,
                        y: current.y,
                        text: trimmed,
                        fontSize: current.fontSize,
                        fill: current.fill,
                        stroke: "transparent",
                        strokeWidth: 0,
                        rotation: 0,
                        scaleX: 1,
                        scaleY: 1,
                    },
                ])
            }
        }
        setEditingText(null)
    }, [elements, onElementsChange])

    const handleStageMouseDown = useCallback(
        (e) => {
            commitEditingText()

            if (tool === WhiteboardTool.SELECT) {
                const clickedOnEmpty = e.target === e.target.getStage()
                if (clickedOnEmpty) {
                    onSelectElement(null)
                }
                return
            }

            if (tool === WhiteboardTool.TEXT) {
                const stage = e.target.getStage()
                const pos = stage.getPointerPosition()
                const newEl = {
                    id: generateElementId(),
                    type: ELEMENT_TYPES.TEXT,
                    x: pos.x,
                    y: pos.y,
                    text: "",
                    fontSize: 18,
                    fill: strokeColor,
                    stroke: "transparent",
                    strokeWidth: 0,
                    rotation: 0,
                    scaleX: 1,
                    scaleY: 1,
                }
                setEditingText({
                    id: newEl.id,
                    x: pos.x,
                    y: pos.y,
                    text: "",
                    fontSize: 18,
                    fill: strokeColor,
                })
                setIsDrawing(false)
                return
            }

            setIsDrawing(true)
            const stage = e.target.getStage()
            const pos = stage.getPointerPosition()

            if (tool === WhiteboardTool.PEN) {
                setDrawingElement({
                    id: generateElementId(),
                    type: ELEMENT_TYPES.PEN,
                    stroke: strokeColor,
                    strokeWidth,
                    points: [pos.x, pos.y],
                    fill: "transparent",
                    tension: 0.5,
                    lineCap: "round",
                    lineJoin: "round",
                    globalCompositeOperation: "source-over",
                })
            } else if (tool === WhiteboardTool.RECTANGLE) {
                setDrawingElement({
                    id: generateElementId(),
                    type: ELEMENT_TYPES.RECTANGLE,
                    x: pos.x,
                    y: pos.y,
                    width: 0,
                    height: 0,
                    fill: "transparent",
                    stroke: strokeColor,
                    strokeWidth,
                    rotation: 0,
                    scaleX: 1,
                    scaleY: 1,
                })
            } else if (tool === WhiteboardTool.CIRCLE) {
                setDrawingElement({
                    id: generateElementId(),
                    type: ELEMENT_TYPES.CIRCLE,
                    x: pos.x,
                    y: pos.y,
                    radius: 0,
                    fill: "transparent",
                    stroke: strokeColor,
                    strokeWidth,
                    rotation: 0,
                    scaleX: 1,
                    scaleY: 1,
                })
            } else if (tool === WhiteboardTool.LINE) {
                setDrawingElement({
                    id: generateElementId(),
                    type: ELEMENT_TYPES.LINE,
                    points: [pos.x, pos.y, pos.x, pos.y],
                    stroke: strokeColor,
                    strokeWidth,
                    fill: "transparent",
                    lineCap: "round",
                    lineJoin: "round",
                    tension: 0,
                })
            } else if (tool === WhiteboardTool.ARROW) {
                setDrawingElement({
                    id: generateElementId(),
                    type: ELEMENT_TYPES.ARROW,
                    points: [pos.x, pos.y, pos.x, pos.y],
                    stroke: strokeColor,
                    strokeWidth,
                    fill: "transparent",
                    lineCap: "round",
                    lineJoin: "round",
                    tension: 0,
                    pointerLength: 10,
                    pointerWidth: 10,
                })
            }
        },
        [tool, strokeColor, strokeWidth, onSelectElement, commitEditingText],
    )

    const handleStageMouseMove = useCallback(
        (e) => {
            if (!isDrawing || !drawingElement) return
            const stage = e.target.getStage()
            const pos = stage.getPointerPosition()

            if (drawingElement.type === ELEMENT_TYPES.PEN) {
                setDrawingElement((prev) => ({
                    ...prev,
                    points: [...prev.points, pos.x, pos.y],
                }))
            } else if (
                drawingElement.type === ELEMENT_TYPES.RECTANGLE
            ) {
                const newX = drawingElement.x
                const newY = drawingElement.y
                const newWidth = pos.x - newX
                const newHeight = pos.y - newY
                setDrawingElement((prev) => ({
                    ...prev,
                    x: newWidth < 0 ? pos.x : newX,
                    y: newHeight < 0 ? pos.y : newY,
                    width: Math.abs(newWidth),
                    height: Math.abs(newHeight),
                }))
            } else if (drawingElement.type === ELEMENT_TYPES.CIRCLE) {
                const dx = pos.x - drawingElement.x
                const dy = pos.y - drawingElement.y
                const radius = Math.sqrt(dx * dx + dy * dy)
                setDrawingElement((prev) => ({
                    ...prev,
                    radius: Math.max(0, radius),
                }))
            } else if (
                drawingElement.type === ELEMENT_TYPES.LINE ||
                drawingElement.type === ELEMENT_TYPES.ARROW
            ) {
                setDrawingElement((prev) => {
                    const pts = [...prev.points]
                    pts[2] = pos.x
                    pts[3] = pos.y
                    return { ...prev, points: pts }
                })
            }
        },
        [isDrawing, drawingElement],
    )

    const handleStageMouseUp = useCallback(() => {
        if (!isDrawing || !drawingElement) {
            setIsDrawing(false)
            return
        }

        const elementToAdd = { ...drawingElement }

        if (
            elementToAdd.type === ELEMENT_TYPES.RECTANGLE &&
            (elementToAdd.width < MIN_SHAPE_SIZE || elementToAdd.height < MIN_SHAPE_SIZE)
        ) {
            setDrawingElement(null)
            setIsDrawing(false)
            return
        }

        if (elementToAdd.type === ELEMENT_TYPES.CIRCLE && elementToAdd.radius < MIN_SHAPE_SIZE / 2) {
            setDrawingElement(null)
            setIsDrawing(false)
            return
        }

        if (
            (elementToAdd.type === ELEMENT_TYPES.LINE || elementToAdd.type === ELEMENT_TYPES.ARROW) &&
            elementToAdd.points
        ) {
            const dx = elementToAdd.points[2] - elementToAdd.points[0]
            const dy = elementToAdd.points[3] - elementToAdd.points[1]
            if (Math.sqrt(dx * dx + dy * dy) < MIN_SHAPE_SIZE) {
                setDrawingElement(null)
                setIsDrawing(false)
                return
            }
        }

        onElementsChange([...elements, elementToAdd])
        onSelectElement(elementToAdd.id)
        setDrawingElement(null)
        setIsDrawing(false)
    }, [isDrawing, drawingElement, elements, onElementsChange, onSelectElement])

    const handleElementDragEnd = useCallback(
        (e, elementId) => {
            const node = e.target
            const updated = elements.map((el) => {
                if (el.id === elementId) {
                    return {
                        ...el,
                        x: node.x(),
                        y: node.y(),
                        rotation: node.rotation(),
                    }
                }
                return el
            })
            onElementsChange(updated)
        },
        [elements, onElementsChange],
    )

    const handleTransformEnd = useCallback(
        (e, elementId) => {
            const node = e.target
            const scaleX = node.scaleX()
            const scaleY = node.scaleY()

            const updated = elements.map((el) => {
                if (el.id === elementId) {
                    const newEl = {
                        ...el,
                        x: node.x(),
                        y: node.y(),
                        rotation: node.rotation(),
                        scaleX: el.scaleX * scaleX,
                        scaleY: el.scaleY * scaleY,
                    }
                    if (el.type === ELEMENT_TYPES.RECTANGLE) {
                        newEl.width = el.width * scaleX
                        newEl.height = el.height * scaleY
                        newEl.scaleX = 1
                        newEl.scaleY = 1
                    }
                    if (el.type === ELEMENT_TYPES.CIRCLE) {
                        newEl.radius = el.radius * Math.max(scaleX, scaleY)
                        newEl.scaleX = 1
                        newEl.scaleY = 1
                    }
                    return newEl
                }
                return el
            })
            onElementsChange(updated)
        },
        [elements, onElementsChange],
    )

    const handleTextDblClick = useCallback((el) => {
        setEditingText({
            id: el.id,
            x: el.x,
            y: el.y,
            text: el.text || "",
            fontSize: el.fontSize || 18,
            fill: el.fill || "#000000",
        })
    }, [])

    const handleTextSubmit = useCallback(
        (value) => {
            if (!editingText) return
            const trimmed = (value || "").trim()
            if (trimmed) {
                const existing = elements.find((el) => el.id === editingText.id)
                if (existing) {
                    const updated = elements.map((el) =>
                        el.id === editingText.id ? { ...el, text: trimmed } : el,
                    )
                    onElementsChange(updated)
                } else {
                    const newTextEl = {
                        id: editingText.id,
                        type: ELEMENT_TYPES.TEXT,
                        x: editingText.x,
                        y: editingText.y,
                        text: trimmed,
                        fontSize: editingText.fontSize,
                        fill: editingText.fill,
                        stroke: "transparent",
                        strokeWidth: 0,
                        rotation: 0,
                        scaleX: 1,
                        scaleY: 1,
                    }
                    onElementsChange([...elements, newTextEl])
                }
                onSelectElement(editingText.id)
            }
            setEditingText(null)
        },
        [editingText, elements, onElementsChange, onSelectElement],
    )

    const handleTextCancel = useCallback(() => {
        setEditingText(null)
    }, [])

    const handleWheel = useCallback(
        (e) => {
            if (e.evt.ctrlKey || e.evt.metaKey) {
                e.evt.preventDefault()
                const delta = e.evt.deltaY > 0 ? -0.1 : 0.1
                const newZoom = Math.max(0.25, Math.min(4, +(zoom + delta).toFixed(2)))
                onZoomChange?.(newZoom)
            }
        },
        [zoom, onZoomChange],
    )

    const handleClickElement = useCallback(
        (el) => {
            onSelectElement(el.id)
        },
        [onSelectElement],
    )

    const renderElement = (el, isPreview = false) => {
        const key = el.id
        const commonProps = {
            key,
            id: el.id,
            x: el.x,
            y: el.y,
            rotation: el.rotation || 0,
            scaleX: isPreview ? 1 : el.scaleX || 1,
            scaleY: isPreview ? 1 : el.scaleY || 1,
        }

        const interactiveProps = isPreview
            ? {}
            : {
                  draggable: tool === WhiteboardTool.SELECT || selectedId === el.id,
                  onClick: () => handleClickElement(el),
                  onTap: () => handleClickElement(el),
                  onDragEnd: (e) => handleElementDragEnd(e, el.id),
                  onTransformEnd: (e) => handleTransformEnd(e, el.id),
              }

        switch (el.type) {
            case ELEMENT_TYPES.RECTANGLE:
                return (
                    <Rect
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        width={el.width}
                        height={el.height}
                        fill={el.fill || "transparent"}
                        stroke={el.stroke}
                        strokeWidth={el.strokeWidth}
                        name={el.id}
                    />
                )
            case ELEMENT_TYPES.CIRCLE:
                return (
                    <Circle
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        radius={el.radius}
                        fill={el.fill || "transparent"}
                        stroke={el.stroke}
                        strokeWidth={el.strokeWidth}
                        name={el.id}
                    />
                )
            case ELEMENT_TYPES.LINE:
                return (
                    <Line
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        points={el.points}
                        stroke={el.stroke}
                        strokeWidth={el.strokeWidth}
                        fill={el.fill || "transparent"}
                        lineCap={el.lineCap || "round"}
                        lineJoin={el.lineJoin || "round"}
                        tension={el.tension || 0}
                        name={el.id}
                    />
                )
            case ELEMENT_TYPES.ARROW:
                return (
                    <Arrow
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        points={el.points}
                        stroke={el.stroke}
                        strokeWidth={el.strokeWidth}
                        fill={el.fill || "transparent"}
                        lineCap={el.lineCap || "round"}
                        lineJoin={el.lineJoin || "round"}
                        pointerLength={el.pointerLength || 10}
                        pointerWidth={el.pointerWidth || 10}
                        name={el.id}
                    />
                )
            case ELEMENT_TYPES.PEN:
                return (
                    <Line
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        points={el.points}
                        stroke={el.stroke}
                        strokeWidth={el.strokeWidth}
                        fill={el.fill || "transparent"}
                        lineCap={el.lineCap || "round"}
                        lineJoin={el.lineJoin || "round"}
                        tension={el.tension || 0.5}
                        globalCompositeOperation={el.globalCompositeOperation || "source-over"}
                        name={el.id}
                    />
                )
            case ELEMENT_TYPES.TEXT:
                return (
                    <Text
                        ref={(node) => { shapeRefs.current[el.id] = node }}
                        {...commonProps}
                        {...interactiveProps}
                        text={el.text || ""}
                        fontSize={el.fontSize || 18}
                        fill={el.fill || "#000000"}
                        onDblClick={() => !isPreview && handleTextDblClick(el)}
                        onDblTap={() => !isPreview && handleTextDblClick(el)}
                        name={el.id}
                    />
                )
            default:
                return null
        }
    }

    const elementsToRender = useMemo(
        () => (drawingElement ? [...elements, drawingElement] : elements),
        [elements, drawingElement],
    )

    return (
        <div ref={containerRef} className="flex-1 relative overflow-hidden">
            <Stage
                ref={stageRef}
                width={stageSize.width}
                height={stageSize.height}
                scaleX={zoom}
                scaleY={zoom}
                onMouseDown={handleStageMouseDown}
                onMouseMove={handleStageMouseMove}
                onMouseUp={handleStageMouseUp}
                onTouchStart={handleStageMouseDown}
                onTouchMove={handleStageMouseMove}
                onTouchEnd={handleStageMouseUp}
                onWheel={handleWheel}
                style={{ background: stageBg }}
            >
                <Layer>
                    <Rect
                        x={0}
                        y={0}
                        width={stageSize.width}
                        height={stageSize.height}
                        fill={stageBg}
                        listening={false}
                    />
                    {elementsToRender.map((el) => renderElement(el, el.id === drawingElement?.id))}
                    {selectedId && !isDrawing && (
                        <Transformer
                            ref={transformerRef}
                            boundBoxFunc={(oldBox, newBox) => {
                                if (newBox.width < 5 || newBox.height < 5) return oldBox
                                return newBox
                            }}
                            rotateEnabled={true}
                            enabledAnchors={["top-left", "top-right", "bottom-left", "bottom-right", "middle-left", "middle-right", "top-center", "bottom-center"]}
                        />
                    )}
                </Layer>
            </Stage>
            {editingText && (
                <CanvasTextInput
                    x={editingText.x}
                    y={editingText.y}
                    text={editingText.text}
                    fontSize={editingText.fontSize}
                    fill={editingText.fill}
                    onSubmit={handleTextSubmit}
                    onCancel={handleTextCancel}
                    onTextChange={(newText) => setEditingText((prev) => (prev ? { ...prev, text: newText } : prev))}
                />
            )}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2">
                <span className="text-[10px] text-muted-foreground bg-background/80 px-2 py-0.5 rounded-sm">
                    {elements.length} element{elements.length !== 1 ? "s" : ""}
                </span>
            </div>
        </div>
    )
}
