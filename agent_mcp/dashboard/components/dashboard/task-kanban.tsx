"use client"

import React, { useState, useCallback } from "react"
import { Task } from "@/lib/api"
import { apiClient } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { useWebSocket } from "@/hooks/useWebSocket"

// Simple drag-and-drop implementation without external library
// Using HTML5 drag and drop API

interface TaskKanbanProps {
  tasks: Task[]
  onTaskUpdate: (taskId: string, updates: Partial<Task>) => Promise<void>
  onRefresh: () => void
}

type TaskStatus = Task['status']

const STATUS_COLUMNS: TaskStatus[] = ['pending', 'in_progress', 'completed', 'cancelled', 'failed']

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  failed: 'Failed'
}

const STATUS_COLORS: Record<TaskStatus, string> = {
  pending: 'bg-gray-100 border-gray-300 text-gray-900',
  in_progress: 'bg-red-100 border-red-300 text-red-900',
  completed: 'bg-gray-200 border-gray-400 text-gray-900',
  cancelled: 'bg-slate-100 border-slate-300 text-slate-900',
  failed: 'bg-red-200 border-red-400 text-red-900'
}

export function TaskKanban({ tasks, onTaskUpdate, onRefresh }: TaskKanbanProps) {
  const [draggedTask, setDraggedTask] = useState<string | null>(null)
  const [dragOverColumn, setDragOverColumn] = useState<TaskStatus | null>(null)

  const handleDragStart = useCallback((e: React.DragEvent, taskId: string) => {
    setDraggedTask(taskId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', taskId)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverColumn(status)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOverColumn(null)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent, targetStatus: TaskStatus) => {
    e.preventDefault()
    setDragOverColumn(null)
    
    const taskId = e.dataTransfer.getData('text/plain')
    if (!taskId || !draggedTask) return

    const task = tasks.find(t => t.task_id === taskId)
    if (!task || task.status === targetStatus) {
      setDraggedTask(null)
      return
    }

    try {
      await onTaskUpdate(taskId, { status: targetStatus })
      onRefresh()
    } catch (error) {
      console.error('Failed to update task status:', error)
    } finally {
      setDraggedTask(null)
    }
  }, [draggedTask, tasks, onTaskUpdate, onRefresh])

  const getTasksByStatus = (status: TaskStatus) => {
    return tasks.filter(task => task.status === status)
  }

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high': return 'bg-red-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4 h-full">
      {STATUS_COLUMNS.map(status => {
        const columnTasks = getTasksByStatus(status)
        const isDragOver = dragOverColumn === status

        return (
          <div
            key={status}
            className={cn(
              "flex-1 min-w-[280px] rounded-lg border-2 transition-colors",
              isDragOver ? "border-red-600 bg-red-50" : "border-gray-200 bg-gray-50",
              "flex flex-col"
            )}
            onDragOver={(e) => handleDragOver(e, status)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, status)}
          >
            <div className={cn(
              "p-3 border-b font-semibold text-sm uppercase tracking-wide",
              STATUS_COLORS[status]
            )}>
              <div className="flex items-center justify-between">
                <span>{STATUS_LABELS[status]}</span>
                <Badge variant="secondary" className="text-xs">
                  {columnTasks.length}
                </Badge>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {columnTasks.map(task => (
                <Card
                  key={task.task_id}
                  className={cn(
                    "cursor-move transition-shadow hover:shadow-md",
                    draggedTask === task.task_id && "opacity-50"
                  )}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.task_id)}
                >
                  <CardHeader className="p-3 pb-2">
                    <CardTitle className="text-sm font-medium line-clamp-2">
                      {task.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3 pt-0">
                    {task.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {task.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between gap-2">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        getPriorityColor(task.priority)
                      )} />
                      {task.assigned_to && (
                        <span className="text-xs text-muted-foreground truncate">
                          {task.assigned_to}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
              {columnTasks.length === 0 && (
                <div className="text-center text-sm text-muted-foreground py-8">
                  No tasks
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

