"use client"

import React, { useState, useEffect } from 'react'
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { X, Trash2 } from 'lucide-react'
import { Task } from '@/lib/api'
import { apiClient } from '@/lib/api'

interface EditTaskModalProps {
  task: Task | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onTaskUpdated: () => void
  onTaskDeleted?: () => void
}

export function EditTaskModal({ 
  task, 
  open, 
  onOpenChange, 
  onTaskUpdated,
  onTaskDeleted 
}: EditTaskModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'pending' as Task['status'],
    priority: 'medium' as Task['priority'],
    assigned_to: '',
    parent_task: '',
    depends_on_tasks: [] as string[],
    tags: [] as string[],
    due_date: '',
    metadata: {} as Record<string, any>
  })
  const [newTag, setNewTag] = useState('')
  const [newDependency, setNewDependency] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Load task data when modal opens
  useEffect(() => {
    if (task && open) {
      setFormData({
        title: task.title || '',
        description: task.description || '',
        status: task.status || 'pending',
        priority: task.priority || 'medium',
        assigned_to: task.assigned_to || '',
        parent_task: task.parent_task || '',
        depends_on_tasks: Array.isArray(task.depends_on_tasks) 
          ? task.depends_on_tasks 
          : typeof task.depends_on_tasks === 'string' 
            ? JSON.parse(task.depends_on_tasks || '[]') 
            : [],
        tags: (task as any).tags || [], // tags may exist in task data but not in type definition
        due_date: (task as any).due_date ? new Date((task as any).due_date).toISOString().split('T')[0] : '',
        metadata: (task as any).metadata || {}
      })
    }
  }, [task, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!task || !formData.title.trim()) return

    setIsSaving(true)
    try {
      const updateData: Partial<Task> = {
        title: formData.title.trim(),
        description: formData.description.trim() || undefined,
        status: formData.status,
        priority: formData.priority,
        assigned_to: formData.assigned_to.trim() || undefined,
        parent_task: formData.parent_task.trim() || undefined,
        depends_on_tasks: formData.depends_on_tasks,
        ...(formData.tags && { tags: formData.tags } as any),
        ...(formData.due_date && { due_date: formData.due_date } as any),
        ...(formData.metadata && { metadata: formData.metadata } as any)
      }

      await apiClient.updateTask(task.task_id, updateData)
      onTaskUpdated()
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to update task:', error)
      alert('Failed to update task. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!task) return

    setIsDeleting(true)
    try {
      await apiClient.deleteTask(task.task_id)
      if (onTaskDeleted) {
        onTaskDeleted()
      }
      onTaskUpdated()
      onOpenChange(false)
      setShowDeleteConfirm(false)
    } catch (error) {
      console.error('Failed to delete task:', error)
      alert('Failed to delete task. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim()) && formData.tags.length < 20) {
      setFormData(prev => ({ ...prev, tags: [...prev.tags, newTag.trim()] }))
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({ 
      ...prev, 
      tags: prev.tags.filter(tag => tag !== tagToRemove) 
    }))
  }

  const addDependency = () => {
    if (newDependency.trim() && !formData.depends_on_tasks.includes(newDependency.trim())) {
      setFormData(prev => ({ 
        ...prev, 
        depends_on_tasks: [...prev.depends_on_tasks, newDependency.trim()] 
      }))
      setNewDependency('')
    }
  }

  const removeDependency = (depToRemove: string) => {
    setFormData(prev => ({ 
      ...prev, 
      depends_on_tasks: prev.depends_on_tasks.filter(dep => dep !== depToRemove) 
    }))
  }

  if (!task) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto bg-card border-border text-card-foreground">
        <DialogHeader>
          <DialogTitle className="text-lg">Edit Task</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Update task details and configuration
          </DialogDescription>
        </DialogHeader>
        
        {showDeleteConfirm ? (
          <div className="space-y-4 py-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <h3 className="font-semibold text-destructive mb-2">Confirm Deletion</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Are you sure you want to delete this task? This action cannot be undone.
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={isDeleting}
                  size="sm"
                >
                  {isDeleting ? 'Deleting...' : 'Delete Task'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                  size="sm"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="title" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Task Title *
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Task title"
                className="bg-background border-border text-foreground mt-1"
                required
              />
            </div>

            <div>
              <Label htmlFor="description" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Description
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Detailed task description..."
                className="bg-background border-border text-foreground mt-1 h-24 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="status" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </Label>
                <Select 
                  value={formData.status} 
                  onValueChange={(value: Task['status']) => setFormData(prev => ({ ...prev, status: value }))}
                >
                  <SelectTrigger className="bg-background border-border text-foreground mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background border-border">
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="priority" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Priority
                </Label>
                <Select 
                  value={formData.priority} 
                  onValueChange={(value: Task['priority']) => setFormData(prev => ({ ...prev, priority: value }))}
                >
                  <SelectTrigger className="bg-background border-border text-foreground mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background border-border">
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="assigned_to" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Assign To
                </Label>
                <Input
                  id="assigned_to"
                  value={formData.assigned_to}
                  onChange={(e) => setFormData(prev => ({ ...prev, assigned_to: e.target.value }))}
                  placeholder="agent-id"
                  className="bg-background border-border text-foreground font-mono text-sm mt-1"
                />
              </div>

              <div>
                <Label htmlFor="due_date" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Due Date
                </Label>
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                  className="bg-background border-border text-foreground mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="parent_task" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Parent Task
              </Label>
              <Input
                id="parent_task"
                value={formData.parent_task}
                onChange={(e) => setFormData(prev => ({ ...prev, parent_task: e.target.value }))}
                placeholder="parent-task-id"
                className="bg-background border-border text-foreground font-mono text-sm mt-1"
              />
            </div>

            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
                Dependencies
              </Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={newDependency}
                  onChange={(e) => setNewDependency(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addDependency())}
                  placeholder="task-id"
                  className="bg-background border-border text-foreground font-mono text-sm"
                />
                <Button type="button" variant="outline" onClick={addDependency} size="sm">
                  Add
                </Button>
              </div>
              {formData.depends_on_tasks.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.depends_on_tasks.map(dep => (
                    <Badge key={dep} variant="outline" className="font-mono text-xs">
                      {dep}
                      <button
                        type="button"
                        onClick={() => removeDependency(dep)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div>
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider block mb-2">
                Tags
              </Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  placeholder="tag-name"
                  className="bg-background border-border text-foreground text-sm"
                  disabled={formData.tags.length >= 20}
                />
                <Button type="button" variant="outline" onClick={addTag} size="sm" disabled={formData.tags.length >= 20}>
                  Add
                </Button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                type="button"
                variant="destructive"
                onClick={() => setShowDeleteConfirm(true)}
                size="sm"
                className="mr-auto"
              >
                <Trash2 className="h-4 w-4 mr-1.5" />
                Delete
              </Button>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} size="sm">
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={isSaving} className="bg-teal-600 hover:bg-teal-700">
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

