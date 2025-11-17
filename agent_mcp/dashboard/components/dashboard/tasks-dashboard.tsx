"use client"

import React, { useState, useEffect, useCallback, useMemo } from "react"
import { 
  CheckSquare, Clock, AlertCircle, Users,
  Search, Plus, MoreVertical, Eye, Play, Pause,
  ArrowUp, ArrowDown, Minus, CheckCircle2, Target, Zap, GitBranch, RefreshCw
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { apiClient, Task } from "@/lib/api"
import { useServerStore } from "@/lib/stores/server-store"
import { cn } from "@/lib/utils"
import { TaskDetailsPanel } from "./task-details-panel"
import { TaskBulkActions } from "./task-bulk-actions"
import { EditTaskModal } from "./modals/edit-task-modal"
import { useWebSocket } from "@/hooks/useWebSocket"
import { TaskKanban } from "./task-kanban"
import { LayoutGrid, Table2 } from "lucide-react"
import { Trash2, Edit2, Check, X } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// Cache for tasks data
const tasksCache = new Map<string, { data: Task[], timestamp: number }>()
const CACHE_DURATION = 30000 // 30 seconds
const REFRESH_INTERVAL = 60000 // 1 minute for background refresh

// Real data hook for tasks with caching
const useTasksData = () => {
  const { activeServerId, servers } = useServerStore()
  const activeServer = servers.find(s => s.id === activeServerId)
  
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetch, setLastFetch] = useState<number>(0)

  const fetchData = useCallback(async (forceRefresh = false) => {
    if (!activeServerId || !activeServer || activeServer.status !== 'connected') {
      setTasks([])
      setError(null)
      setLoading(false)
      return
    }

    const cacheKey = `${activeServerId}-tasks`
    const now = Date.now()
    const cached = tasksCache.get(cacheKey)

    // Use cache if it's fresh and not forcing refresh
    if (!forceRefresh && cached && (now - cached.timestamp) < CACHE_DURATION) {
      setTasks(cached.data)
      setError(null)
      setLoading(false)
      return
    }

    // Only show loading on first fetch or force refresh
    if (tasks.length === 0 || forceRefresh) {
      setLoading(true)
    }

    try {
      const tasksData = await apiClient.getTasks()
      
      // Update cache
      tasksCache.set(cacheKey, { data: tasksData, timestamp: now })
      
      setTasks(tasksData)
      setError(null)
      setLastFetch(now)
    } catch (err) {
      // Don't set error state for no server connection - that's handled by DashboardWrapper
      if (err instanceof Error && err.message !== 'NO_SERVER_CONNECTED') {
        setError(err.message)
        console.error('Error fetching tasks:', err)
      }
    } finally {
      setLoading(false)
    }
  }, [activeServerId, activeServer, tasks.length])

  useEffect(() => {
    fetchData()

    // Background refresh - less frequent and doesn't show loading
    const interval = setInterval(() => {
      fetchData(false)
    }, REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [fetchData])

  // WebSocket for real-time updates
  const wsUrl = activeServer && activeServer.status === 'connected' 
    ? `/ws/tasks` 
    : null
  useWebSocket<{ type: string; task_id: string; changes: Partial<Task>; timestamp: string }>(
    wsUrl,
    useCallback((message) => {
      if (message.type === 'task_update') {
        // Update task in local state
        setTasks(prevTasks => {
          const updated = prevTasks.map(task => 
            task.task_id === message.task_id
              ? { ...task, ...message.changes }
              : task
          )
          // If task not found, refresh from server
          if (!updated.find(t => t.task_id === message.task_id)) {
            fetchData(true)
          }
          return updated
        })
      }
    }, [fetchData]),
    {
      reconnect: true,
      reconnectInterval: 3000
    }
  )

  // Manual refresh function
  const refresh = useCallback(() => fetchData(true), [fetchData])

  // Memoize return value to prevent unnecessary re-renders
  return useMemo(() => ({
    tasks, 
    loading, 
    error, 
    refresh,
    lastFetch,
    isConnected: !!activeServerId && activeServer?.status === 'connected' 
  }), [tasks, loading, error, refresh, lastFetch, activeServerId, activeServer])
}

const StatusDot = React.memo(({ status }: { status: Task['status'] }) => {
  const config = {
    in_progress: "bg-red-600 shadow-red-600/50 shadow-md animate-pulse",
    pending: "bg-gray-400 shadow-gray-400/50 shadow-md",
    completed: "bg-gray-500 shadow-gray-500/50 shadow-md",
    cancelled: "bg-slate-500 shadow-slate-500/50 shadow-md",
    failed: "bg-red-700 shadow-red-700/50 shadow-md animate-pulse",
  }
  
  return (
    <div className={cn(
      "w-2.5 h-2.5 rounded-full",
      config[status] || config.pending
    )} />
  )
})
StatusDot.displayName = 'StatusDot'

const PriorityIcon = React.memo(({ priority }: { priority: Task['priority'] }) => {
  const config = {
    high: { icon: ArrowUp, className: "text-orange-400" },
    medium: { icon: Minus, className: "text-amber-400" },
    low: { icon: ArrowDown, className: "text-slate-400" },
  }
  
  const configItem = config[priority] || config.medium // fallback to medium if priority is undefined
  const { icon: Icon, className } = configItem
  return <Icon className={cn("h-4 w-4", className)} />
})
PriorityIcon.displayName = 'PriorityIcon'

const CompactTaskRow = React.memo(({ 
  task, 
  onTaskClick, 
  onUpdateTask, 
  onDeleteTask 
}: { 
  task: Task
  onTaskClick: (task: Task) => void
  onUpdateTask?: (taskId: string, updates: Partial<Task>) => Promise<void>
  onDeleteTask?: (taskId: string) => Promise<void>
}) => {
  const [mounted, setMounted] = useState(false)
  const [editingTitle, setEditingTitle] = useState(false)
  const [editingStatus, setEditingStatus] = useState(false)
  const [editingPriority, setEditingPriority] = useState(false)
  const [tempTitle, setTempTitle] = useState(task.title)
  const [tempStatus, setTempStatus] = useState(task.status)
  const [tempPriority, setTempPriority] = useState(task.priority)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    setTempTitle(task.title)
    setTempStatus(task.status)
    setTempPriority(task.priority)
  }, [task.title, task.status, task.priority])

  const formatDate = useCallback((dateString: string) => {
    if (!mounted) return "..."
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }, [mounted])

  const handleSaveTitle = async () => {
    if (tempTitle.trim() && tempTitle !== task.title && onUpdateTask) {
      setIsUpdating(true)
      try {
        await onUpdateTask(task.task_id, { title: tempTitle.trim() })
        setEditingTitle(false)
      } catch (error) {
        console.error('Failed to update title:', error)
        setTempTitle(task.title) // Revert on error
      } finally {
        setIsUpdating(false)
      }
    } else {
      setEditingTitle(false)
      setTempTitle(task.title)
    }
  }

  const handleSaveStatus = async (newStatus: Task['status']) => {
    if (newStatus !== task.status && onUpdateTask) {
      setIsUpdating(true)
      try {
        await onUpdateTask(task.task_id, { status: newStatus })
        setEditingStatus(false)
      } catch (error) {
        console.error('Failed to update status:', error)
        setTempStatus(task.status) // Revert on error
      } finally {
        setIsUpdating(false)
      }
    } else {
      setEditingStatus(false)
    }
  }

  const handleSavePriority = async (newPriority: Task['priority']) => {
    if (newPriority !== task.priority && onUpdateTask) {
      setIsUpdating(true)
      try {
        await onUpdateTask(task.task_id, { priority: newPriority })
        setEditingPriority(false)
      } catch (error) {
        console.error('Failed to update priority:', error)
        setTempPriority(task.priority) // Revert on error
      } finally {
        setIsUpdating(false)
      }
    } else {
      setEditingPriority(false)
    }
  }

  const handleDelete = async () => {
    if (onDeleteTask) {
      try {
        await onDeleteTask(task.task_id)
        setShowDeleteConfirm(false)
      } catch (error) {
        console.error('Failed to delete task:', error)
      }
    }
  }

  return (
    <>
      <TableRow className="border-red-500/10 dark:border-red-500/10 border-red-600/20 hover:bg-red-500/5 dark:hover:bg-red-500/5 hover:bg-red-600/10 group transition-all duration-200" onClick={() => !editingTitle && !editingStatus && !editingPriority && onTaskClick(task)}>
        <TableCell className="py-3">
          <div className="flex items-center gap-3">
            <StatusDot status={task.status} />
            <PriorityIcon priority={task.priority} />
            <div className="min-w-0 flex-1">
              {editingTitle ? (
                <div className="flex items-center gap-1">
                  <Input
                    value={tempTitle}
                    onChange={(e) => setTempTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveTitle()
                      if (e.key === 'Escape') {
                        setEditingTitle(false)
                        setTempTitle(task.title)
                      }
                    }}
                    onBlur={handleSaveTitle}
                    className="h-7 text-sm font-medium"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                    disabled={isUpdating}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleSaveTitle()
                    }}
                    disabled={isUpdating}
                  >
                    <Check className="h-3 w-3 text-green-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditingTitle(false)
                      setTempTitle(task.title)
                    }}
                    disabled={isUpdating}
                  >
                    <X className="h-3 w-3 text-red-500" />
                  </Button>
                </div>
              ) : (
                <div 
                  className="font-medium text-sm text-foreground truncate cursor-pointer hover:text-red-600 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation()
                    setEditingTitle(true)
                  }}
                  title="Click to edit"
                >
                  {task.title}
                </div>
              )}
              <div className="text-xs text-muted-foreground font-mono">#{task.task_id.slice(-6)}</div>
            </div>
          </div>
        </TableCell>
        
        <TableCell className="py-3">
          {editingStatus ? (
            <Select
              value={tempStatus}
              onValueChange={(value: Task['status']) => {
                setTempStatus(value)
                handleSaveStatus(value)
              }}
              onOpenChange={(open) => {
                if (!open && tempStatus === task.status) {
                  setEditingStatus(false)
                }
              }}
            >
              <SelectTrigger className="h-7 text-xs" onClick={(e) => e.stopPropagation()}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent onClick={(e) => e.stopPropagation()}>
                <SelectItem value="pending">PENDING</SelectItem>
                <SelectItem value="in_progress">IN PROGRESS</SelectItem>
                <SelectItem value="completed">COMPLETED</SelectItem>
                <SelectItem value="cancelled">CANCELLED</SelectItem>
                <SelectItem value="failed">FAILED</SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <Badge 
              variant="outline" 
              className={cn(
                "text-xs font-semibold border-0 px-3 py-1.5 rounded-md cursor-pointer hover:opacity-80 transition-opacity",
                task.status === 'in_progress' && "bg-red-600/15 text-red-600 dark:text-red-400 ring-1 ring-red-600/20",
                task.status === 'pending' && "bg-gray-500/15 text-gray-600 dark:text-gray-400 ring-1 ring-gray-500/20",
                task.status === 'completed' && "bg-gray-600/15 text-gray-700 dark:text-gray-300 ring-1 ring-gray-600/20",
                task.status === 'cancelled' && "bg-slate-500/15 text-slate-500 dark:text-slate-300 ring-1 ring-slate-500/20",
                task.status === 'failed' && "bg-red-700/15 text-red-700 dark:text-red-500 ring-1 ring-red-700/20"
              )}
              onClick={(e) => {
                e.stopPropagation()
                setEditingStatus(true)
              }}
              title="Click to edit"
            >
              {task.status.replace('_', ' ').toUpperCase()}
            </Badge>
          )}
        </TableCell>
      
      <TableCell className="py-3 max-w-xs">
        <div className="text-sm text-foreground truncate">
          {task.description || "No description"}
        </div>
        {task.assigned_to && (
          <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            <Users className="h-3 w-3" />
            {task.assigned_to}
          </div>
        )}
      </TableCell>
      
      <TableCell className="py-3">
        {editingPriority ? (
          <Select
            value={tempPriority}
            onValueChange={(value: Task['priority']) => {
              setTempPriority(value)
              handleSavePriority(value)
            }}
            onOpenChange={(open) => {
              if (!open && tempPriority === task.priority) {
                setEditingPriority(false)
              }
            }}
          >
            <SelectTrigger className="h-7 text-xs" onClick={(e) => e.stopPropagation()}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent onClick={(e) => e.stopPropagation()}>
              <SelectItem value="low">LOW</SelectItem>
              <SelectItem value="medium">MEDIUM</SelectItem>
              <SelectItem value="high">HIGH</SelectItem>
              <SelectItem value="critical">CRITICAL</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <Badge 
            variant="outline" 
            className={cn(
              "text-xs font-medium px-2 py-0.5 cursor-pointer hover:opacity-80 transition-opacity",
              task.priority === 'high' && "bg-orange-500/10 text-orange-500 dark:text-orange-300 border-orange-500/20",
              task.priority === 'medium' && "bg-amber-500/10 text-amber-500 dark:text-amber-300 border-amber-500/20",
              task.priority === 'low' && "bg-slate-500/10 text-slate-500 dark:text-slate-300 border-slate-500/20",
              ((task as any).priority === 'critical') && "bg-red-500/10 text-red-500 dark:text-red-300 border-red-500/20"
            )}
            onClick={(e) => {
              e.stopPropagation()
              setEditingPriority(true)
            }}
            title="Click to edit"
          >
            {task.priority.toUpperCase()}
          </Badge>
        )}
      </TableCell>
      
      <TableCell className="py-3">
        <div className="flex flex-wrap gap-1">
          {task.parent_task && (
            <Badge variant="outline" className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-500 dark:text-purple-300 border-purple-500/20">
              <GitBranch className="h-3 w-3 mr-1" />
              Subtask
            </Badge>
          )}
          {task.child_tasks && task.child_tasks.length > 0 && (
            <Badge variant="outline" className="text-xs px-2 py-0.5 bg-red-600/10 text-red-600 dark:text-red-400 border-red-600/20">
              {task.child_tasks.length} children
            </Badge>
          )}
        </div>
      </TableCell>
      
      <TableCell className="py-3 text-xs text-muted-foreground font-mono">
        {formatDate(task.updated_at)}
      </TableCell>
      
      <TableCell className="py-3">
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground hover:bg-muted"
            onClick={(e) => {
              e.stopPropagation()
              onTaskClick(task)
            }}
          >
            <Eye className="h-3.5 w-3.5" />
          </Button>
          {task.status === 'pending' && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-7 w-7 p-0 text-red-600 hover:text-red-500 hover:bg-red-600/10"
              onClick={(e) => {
                e.stopPropagation()
                handleSaveStatus('in_progress')
              }}
              disabled={isUpdating}
            >
              <Play className="h-3.5 w-3.5" />
            </Button>
          )}
          {task.status === 'in_progress' && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-7 w-7 p-0 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
              onClick={(e) => {
                e.stopPropagation()
                handleSaveStatus('completed')
              }}
              disabled={isUpdating}
            >
              <Pause className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
            onClick={(e) => {
              e.stopPropagation()
              setShowDeleteConfirm(true)
            }}
            disabled={isUpdating}
            title="Delete task"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
    
    <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
      <AlertDialogContent onClick={(e) => e.stopPropagation()}>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Task</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete "{task.title}"? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={(e) => e.stopPropagation()}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.stopPropagation()
              handleDelete()
            }}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </>
  )
}, (prevProps, nextProps) => {
  // Only re-render if the task actually changed
  return JSON.stringify(prevProps.task) === JSON.stringify(nextProps.task) &&
         prevProps.onUpdateTask === nextProps.onUpdateTask &&
         prevProps.onDeleteTask === nextProps.onDeleteTask
})
CompactTaskRow.displayName = 'CompactTaskRow'

const StatsCard = React.memo(({ icon: Icon, label, value, change, trend }: {
  icon: any
  label: string
  value: number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
}) => (
  <div className="bg-slate-900/60 dark:bg-slate-900/60 bg-white/80 border border-slate-800/60 dark:border-slate-800/60 border-slate-200 rounded-xl p-[var(--space-fluid-md)] backdrop-blur-sm hover:bg-slate-900/80 dark:hover:bg-slate-900/80 hover:bg-white/90 transition-all duration-200 group">
    <div className="flex items-center justify-between">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Icon className="h-4 w-4 text-slate-400 dark:text-slate-400 text-slate-600 group-hover:text-slate-300 dark:group-hover:text-slate-300 group-hover:text-slate-700 transition-colors" />
          <span className="text-fluid-xs font-semibold text-slate-400 dark:text-slate-400 text-slate-600 uppercase tracking-wider">{label}</span>
        </div>
        <div className="text-fluid-2xl font-bold text-white dark:text-white text-slate-900 mb-1">{value}</div>
        {change && (
          <div className={cn(
            "text-fluid-xs font-medium",
            trend === 'up' && "text-red-600",
            trend === 'down' && "text-orange-400",
            trend === 'neutral' && "text-slate-400"
          )}>
            {change}
          </div>
        )}
      </div>
    </div>
  </div>
))
StatsCard.displayName = 'StatsCard'

const CreateTaskModal = React.memo(({ onCreateTask }: { onCreateTask: (data: any) => void }) => {
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as Task['priority'],
    assigned_to: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) return

    onCreateTask({
      title: formData.title.trim(),
      description: formData.description.trim() || undefined,
      priority: formData.priority,
      assigned_to: formData.assigned_to.trim() || undefined
    })

    setFormData({ title: '', description: '', priority: 'medium', assigned_to: '' })
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white shadow-lg hover:shadow-red-600/25 transition-all duration-200">
          <Plus className="h-4 w-4 mr-1.5" />
          Create Task
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-card border-border text-card-foreground">
        <DialogHeader>
          <DialogTitle className="text-lg">Create Task</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Define a new task for the system to execute.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
              Task Title
            </label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Analyze dataset and generate report"
              className="bg-background border-border text-foreground"
              required
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
              Description
            </label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Detailed task requirements and objectives..."
              className="bg-background border-border text-foreground h-20 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
                Priority
              </label>
              <Select value={formData.priority} onValueChange={(value: Task['priority']) => setFormData(prev => ({ ...prev, priority: value }))}>
                <SelectTrigger className="bg-background border-border text-foreground">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border-border">
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
                Assign To
              </label>
              <Input
                value={formData.assigned_to}
                onChange={(e) => setFormData(prev => ({ ...prev, assigned_to: e.target.value }))}
                placeholder="agent-01"
                className="bg-background border-border text-foreground font-mono text-sm"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} size="sm">
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-red-600 hover:bg-red-700 shadow-lg hover:shadow-red-600/25 transition-all">
              Create Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
})
CreateTaskModal.displayName = 'CreateTaskModal'

export function TasksDashboard() {
  const { tasks, loading, error, refresh, lastFetch, isConnected } = useTasksData()
  const { servers, activeServerId } = useServerStore()
  const activeServer = servers.find(s => s.id === activeServerId)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [editTaskModalOpen, setEditTaskModalOpen] = useState(false)
  const [taskToEdit, setTaskToEdit] = useState<Task | null>(null)
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table')

  // Memoize filtered tasks to prevent unnecessary recalculations
  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (task.description && task.description.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter
      const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter
      return matchesSearch && matchesStatus && matchesPriority
    })
  }, [tasks, searchTerm, statusFilter, priorityFilter])

  // Memoize stats calculation
  const stats = useMemo(() => ({
    total: tasks.length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    pending: tasks.filter(t => t.status === 'pending').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  }), [tasks])

  const handleCreateTask = useCallback(async (data: any) => {
    try {
      await apiClient.createTask(data)
      // Refresh tasks after creating a new one
      refresh()
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }, [refresh])

  const handleTaskClick = useCallback((task: Task) => {
    setSelectedTask(task)
  }, [])

  const handleCloseTaskPanel = useCallback(() => {
    setSelectedTask(null)
  }, [])

  const handleUpdateTask = useCallback(async (taskId: string, updates: Partial<Task>) => {
    try {
      await apiClient.updateTask(taskId, updates)
      refresh()
    } catch (error) {
      console.error('Failed to update task:', error)
      throw error
    }
  }, [refresh])

  const handleDeleteTask = useCallback(async (taskId: string) => {
    try {
      await apiClient.deleteTask(taskId)
      refresh()
      if (selectedTask?.task_id === taskId) {
        setSelectedTask(null)
      }
    } catch (error) {
      console.error('Failed to delete task:', error)
      throw error
    }
  }, [refresh, selectedTask])

  const handleEditTask = useCallback((task: Task) => {
    setTaskToEdit(task)
    setEditTaskModalOpen(true)
  }, [])

  const handleBulkOperation = useCallback(async (operation: string, value?: any) => {
    if (selectedTaskIds.size === 0) return

    try {
      // Use bulk update endpoint if available
      for (const taskId of Array.from(selectedTaskIds)) {
        switch (operation) {
          case 'delete':
            await handleDeleteTask(taskId)
            break
          case 'update_status':
            if (value) await handleUpdateTask(taskId, { status: value })
            break
          case 'update_priority':
            if (value) await handleUpdateTask(taskId, { priority: value })
            break
          case 'assign':
            if (value) await handleUpdateTask(taskId, { assigned_to: value })
            break
        }
      }
      setSelectedTaskIds(new Set())
      refresh()
    } catch (error) {
      console.error('Bulk operation failed:', error)
    }
  }, [selectedTaskIds, handleUpdateTask, handleDeleteTask, refresh])

  const toggleTaskSelection = useCallback((taskId: string) => {
    setSelectedTaskIds(prev => {
      const next = new Set(prev)
      if (next.has(taskId)) {
        next.delete(taskId)
      } else {
        next.add(taskId)
      }
      return next
    })
  }, [])

  if (!isConnected) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <CheckSquare className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">No Server Connection</h3>
            <p className="text-muted-foreground text-sm">Connect to an MCP server to manage tasks</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto" />
          <p className="text-muted-foreground text-sm">Loading tasks...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">Connection Error</h3>
            <p className="text-destructive text-sm">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full space-y-[var(--space-fluid-lg)]" style={{
      paddingRight: selectedTask ? `calc(420px)` : '0px',
      transition: 'padding-right 0.5s ease-in-out'
    }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-fluid-2xl font-bold text-white dark:text-white text-slate-900">Task Operations</h1>
          <p className="text-slate-400 dark:text-slate-400 text-slate-600 text-fluid-base mt-1">Orchestrate and monitor autonomous tasks</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <Badge variant="outline" className="text-xs bg-red-600/15 text-red-600 border-red-600/30 font-medium">
            <div className="w-2 h-2 bg-red-600 rounded-full mr-2 animate-pulse" />
            {activeServer?.name}
          </Badge>
          {lastFetch > 0 && (
            <span className="text-xs text-muted-foreground">
              Last updated: {new Date(lastFetch).toLocaleTimeString()}
            </span>
          )}
          <div className="flex items-center gap-2 border rounded-md overflow-hidden">
            <Button
              variant={viewMode === 'table' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('table')}
              className={cn(
                "rounded-none border-0 h-8 px-3 text-xs",
                viewMode === 'table' && "bg-primary text-primary-foreground"
              )}
            >
              <Table2 className="h-3.5 w-3.5 mr-1.5" />
              Table
            </Button>
            <Button
              variant={viewMode === 'kanban' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('kanban')}
              className={cn(
                "rounded-none border-0 h-8 px-3 text-xs",
                viewMode === 'kanban' && "bg-primary text-primary-foreground"
              )}
            >
              <LayoutGrid className="h-3.5 w-3.5 mr-1.5" />
              Kanban
            </Button>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={refresh}
            disabled={loading}
            className="text-xs"
          >
            <RefreshCw className={cn("h-3.5 w-3.5 mr-1.5", loading && "animate-spin")} />
            Refresh
          </Button>
          <CreateTaskModal onCreateTask={handleCreateTask} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-[var(--space-fluid-md)] grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatsCard 
          icon={Target} 
          label="Total" 
          value={stats.total} 
          change={stats.total > 0 ? `${stats.in_progress} active` : undefined}
          trend="neutral"
        />
        <StatsCard 
          icon={Zap} 
          label="Active" 
          value={stats.in_progress} 
          change={stats.total > 0 ? `${Math.round((stats.in_progress/stats.total)*100)}%` : "0%"}
          trend="up"
        />
        <StatsCard 
          icon={Clock} 
          label="Pending" 
          value={stats.pending} 
          change={stats.pending > 0 ? "Queued" : "None"}
          trend="neutral"
        />
        <StatsCard 
          icon={CheckCircle2} 
          label="Completed" 
          value={stats.completed} 
          change={stats.total > 0 ? `${Math.round((stats.completed/stats.total)*100)}% done` : "0%"}
          trend="up"
        />
        <StatsCard 
          icon={AlertCircle} 
          label="Failed" 
          value={stats.failed} 
          change={stats.failed > 0 ? "Need review" : "All good"}
          trend={stats.failed > 0 ? "down" : "neutral"}
        />
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-[var(--space-fluid-sm)]">
        <div className="relative flex-1 sm:max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-red-600 dark:text-red-600 text-red-600" />
          <Input
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-slate-900/60 dark:bg-slate-900/60 bg-white/80 border-slate-700/60 dark:border-slate-700/60 border-slate-300 text-white dark:text-white text-slate-900 placeholder:text-slate-400 focus:border-red-600/50 focus:ring-red-600/20 transition-all"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-36 bg-slate-900/60 dark:bg-slate-900/60 bg-white/80 border-slate-700/60 dark:border-slate-700/60 border-slate-300 text-white dark:text-white text-slate-900">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 dark:bg-slate-900 bg-white border-slate-800 dark:border-slate-800 border-slate-200">
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-full sm:w-32 bg-slate-900/60 dark:bg-slate-900/60 bg-white/80 border-slate-700/60 dark:border-slate-700/60 border-slate-300 text-white dark:text-white text-slate-900">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 dark:bg-slate-900 bg-white border-slate-800 dark:border-slate-800 border-slate-200">
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Tasks View */}
      {viewMode === 'kanban' ? (
        <div className="bg-slate-900/50 dark:bg-slate-900/50 bg-white/90 border border-red-600/20 dark:border-red-600/20 border-red-600/30 rounded-xl overflow-hidden backdrop-blur-md shadow-xl shadow-red-600/10 h-[calc(100vh-400px)]">
          <TaskKanban
            tasks={filteredTasks}
            onTaskUpdate={handleUpdateTask}
            onRefresh={refresh}
          />
        </div>
      ) : (
        <div className="bg-slate-900/50 dark:bg-slate-900/50 bg-white/90 border border-red-600/20 dark:border-red-600/20 border-red-600/30 rounded-xl overflow-x-auto backdrop-blur-md shadow-xl shadow-red-600/10">
          <Table>
          <TableHeader>
            <TableRow className="border-red-600/10 dark:border-red-600/10 border-red-600/20 hover:bg-transparent">
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Task</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Status</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Details</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Priority</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Relations</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider">Updated</TableHead>
              <TableHead className="text-white/70 dark:text-white/70 text-slate-700 font-medium text-xs uppercase tracking-wider w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTasks.map((task) => (
              <CompactTaskRow
                key={task.task_id}
                task={task}
                onTaskClick={handleTaskClick}
                onUpdateTask={handleUpdateTask}
                onDeleteTask={handleDeleteTask}
              />
            ))}
          </TableBody>
        </Table>
        
        {filteredTasks.length === 0 && (
          <div className="p-12 text-center">
            <CheckSquare className="h-12 w-12 text-red-600/50 dark:text-red-600/50 text-red-600/50 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white dark:text-white text-slate-900 mb-2">No tasks found</h3>
            <p className="text-white/60 dark:text-white/60 text-slate-600 text-sm mb-4">
              {tasks.length === 0 ? "Create your first task to get started" : "No tasks match your current filters"}
            </p>
            {tasks.length === 0 && <CreateTaskModal onCreateTask={handleCreateTask} />}
          </div>
        )}
        </div>
      )}
      
      {/* Bulk Actions */}
      {selectedTaskIds.size > 0 && (
        <TaskBulkActions
          selectedTasks={tasks.filter(t => selectedTaskIds.has(t.task_id))}
          onBulkUpdate={handleBulkOperation}
          onClearSelection={() => setSelectedTaskIds(new Set())}
        />
      )}
      
      {/* Legacy bulk actions UI (can be removed if TaskBulkActions works well) */}
      {false && selectedTaskIds.size > 0 && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-background border border-border rounded-lg shadow-lg p-4 z-50 flex items-center gap-3">
          <span className="text-sm font-medium">
            {selectedTaskIds.size} task{selectedTaskIds.size > 1 ? 's' : ''} selected
          </span>
          <Select onValueChange={(value) => {
            if (value === 'delete') {
              if (confirm(`Delete ${selectedTaskIds.size} task(s)?`)) {
                handleBulkOperation('delete')
              }
            } else if (value.startsWith('status:')) {
              handleBulkOperation('update_status', value.replace('status:', ''))
            } else if (value.startsWith('priority:')) {
              handleBulkOperation('update_priority', value.replace('priority:', ''))
            }
          }}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Bulk actions..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="status:in_progress">Set In Progress</SelectItem>
              <SelectItem value="status:completed">Set Completed</SelectItem>
              <SelectItem value="priority:high">Set High Priority</SelectItem>
              <SelectItem value="priority:low">Set Low Priority</SelectItem>
              <SelectItem value="delete">Delete Selected</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedTaskIds(new Set())}
          >
            Clear
          </Button>
        </div>
      )}

      {/* Task Details Panel */}
      <TaskDetailsPanel 
        task={selectedTask} 
        onClose={handleCloseTaskPanel}
        onEdit={() => {
          if (selectedTask) {
            handleEditTask(selectedTask)
          }
        }}
      />

      {/* Edit Task Modal */}
      <EditTaskModal
        task={taskToEdit}
        open={editTaskModalOpen}
        onOpenChange={setEditTaskModalOpen}
        onTaskUpdated={refresh}
        onTaskDeleted={() => {
          if (taskToEdit?.task_id === selectedTask?.task_id) {
            setSelectedTask(null)
          }
        }}
      />
    </div>
  )
}