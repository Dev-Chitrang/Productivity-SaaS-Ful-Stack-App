import * as React from "react"
import { Tooltip as TooltipPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function TooltipProvider({ delayDuration = 300, ...props }) {
  return <TooltipPrimitive.Provider delayDuration={delayDuration} {...props} />;
}

function Tooltip({ ...props }) {
  return <TooltipPrimitive.Root {...props} />;
}

function TooltipTrigger({ ...props }) {
  return <TooltipPrimitive.Trigger {...props} />;
}

function TooltipContent({
  className,
  sideOffset = 4,
  ...props
}) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          "z-50 overflow-hidden rounded-md bg-foreground px-2 py-1.5 text-xs text-background shadow-md animate-in fade-in-0 zoom-in-95 data-side=bottom:slide-in-from-top-1 data-side=left:slide-in-from-right-1 data-side=right:slide-in-from-left-1 data-side=top:slide-in-from-bottom-1",
          className
        )}
        {...props} />
    </TooltipPrimitive.Portal>
  );
}

export { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent }
