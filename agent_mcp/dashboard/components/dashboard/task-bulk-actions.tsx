"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Trash2, CheckCircle2, ArrowUp, Users, X } from "lucide-react"
import { Task } from "@/lib/api"

interface TaskBulkActionsProps {
  selectedTasks: Task[]
  onBulkUpdate: (operation: string, value?: any) => Promise<void>
  onClearSelection: () => void
}

export function TaskBulkActions({
  selectedTasks,
  onBulkUpdate,
  onClearSelection
}: TaskBulkActionsProps) {
  const [statusValue, setStatusValue] = React.useState<string>("")
  const [priorityValue, setPriorityValue] = React.useState<string>("")
  const [assignValue, setAssignValue] = React.useState<string>("")

  if (selectedTasks.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-background border border-border rounded-lg shadow-lg p-4 z-50 flex items-center gap-3 max-w-4xl">
      <span className="text-sm font-medium">
        {selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''} selected
      </span>
      
      <div className="flex items-center gap-2 flex-wrap">
        <Select value={statusValue} onValueChange={setStatusValue}>
          <SelectTrigger className="w-[140px] h-8 text-xs">
            <SelectValue placeholder="Set Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        {statusValue && (
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              await onBulkUpdate('update_status', statusValue)
              setStatusValue("")
            }}
            className="h-8 text-xs"
          >
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Apply Status
          </Button>
        )}

        <Select value={priorityValue} onValueChange={setPriorityValue}>
          <SelectTrigger className="w-[120px] h-8 text-xs">
            <SelectValue placeholder="Set Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
          </SelectContent>
        </Select>
        {priorityValue && (
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              await onBulkUpdate('update_priority', priorityValue)
              setPriorityValue("")
            }}
            className="h-8 text-xs"
          >
            <ArrowUp className="h-3 w-3 mr-1" />
            Apply Priority
          </Button>
        )}

        <Button
          size="sm"
          variant="destructive"
          onClick={async () => {
            if (confirm(`Delete ${selectedTasks.length} task(s)?`)) {
              await onBulkUpdate('delete')
            }
          }}
          className="h-8 text-xs"
        >
          <Trash2 className="h-3 w-3 mr-1" />
          Delete
        </Button>

        <Button
          size="sm"
          variant="ghost"
          onClick={onClearSelection}
          className="h-8 text-xs"
        >
          <X className="h-3 w-3 mr-1" />
          Clear
        </Button>
      </div>
    </div>
  )
}

