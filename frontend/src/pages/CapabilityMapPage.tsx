import * as React from "react";
import { Plus, Search, Edit, Trash2, Users, TrendingUp, ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";
import { VectorSearchInput } from "@/components/ui/vector-search-input";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient, type Capability, type VectorSearchResult, type CreateCapabilityRequest, type CapabilityRecommendation } from "@/lib/api";
import { toast } from "sonner";

export function CapabilityMapPage() {
  const [capabilities, setCapabilities] = React.useState<Capability[]>([]);
  const [filteredCapabilities, setFilteredCapabilities] = React.useState<Capability[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [searchLoading, setSearchLoading] = React.useState(false);
  const [searchResults, setSearchResults] = React.useState<VectorSearchResult[]>([]);
  const [selectedCapability, setSelectedCapability] = React.useState<Capability | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = React.useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [importanceFilter, setImportanceFilter] = React.useState<string>("all");
  const [blockingRecommendations, setBlockingRecommendations] = React.useState<CapabilityRecommendation[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = React.useState(false);

  // Form state for create/edit
  const [formData, setFormData] = React.useState<CreateCapabilityRequest>({
    name: "",
    description: "",
    parent: null,
    status: "CURRENT",
    strategic_importance: "MEDIUM",
    owner: "",
    notes: ""
  });

  React.useEffect(() => {
    loadCapabilities();
  }, []);

  React.useEffect(() => {
    filterCapabilities();
  }, [capabilities, searchQuery, statusFilter, importanceFilter]);

  const loadCapabilities = async () => {
    try {
      const response = await apiClient.getCapabilities();
      setCapabilities(response.results);
    } catch (error) {
      toast.error("Failed to load capabilities");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const filterCapabilities = () => {
    let filtered = capabilities;

    // Text search
    if (searchQuery) {
      filtered = filtered.filter(cap => 
        cap.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cap.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cap.owner?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter(cap => cap.status === statusFilter);
    }

    // Importance filter
    if (importanceFilter !== "all") {
      filtered = filtered.filter(cap => cap.strategic_importance === importanceFilter);
    }

    setFilteredCapabilities(filtered);
  };

  const handleVectorSearch = async (query: string) => {
    setSearchLoading(true);
    try {
      const response = await apiClient.searchCapabilities({ query, limit: 8, threshold: 0.5 });
      setSearchResults(response.results);
      toast.success(`Found ${response.results.length} similar capabilities`);
    } catch (error) {
      toast.error("Vector search failed");
      console.error(error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await apiClient.createCapability(formData);
      toast.success("Capability created successfully");
      setIsCreateDialogOpen(false);
      resetForm();
      loadCapabilities();
    } catch (error) {
      toast.error("Failed to create capability");
      console.error(error);
    }
  };

  const handleEdit = async () => {
    if (!selectedCapability) return;
    
    try {
      await apiClient.updateCapability(selectedCapability.id, formData);
      toast.success("Capability updated successfully");
      setIsEditDialogOpen(false);
      resetForm();
      loadCapabilities();
    } catch (error) {
      toast.error("Failed to update capability");
      console.error(error);
    }
  };

  const handleDelete = async (capability: Capability) => {
    try {
      await apiClient.deleteCapability(capability.id);
      toast.success("Capability archived successfully");
      loadCapabilities();
    } catch (error) {
      toast.error("Failed to delete capability");
      console.error(error);
    }
  };

  const handlePermanentDelete = async (capability: Capability) => {
    try {
      const result = await apiClient.permanentDeleteCapability(capability.id);
      toast.success(result.message || "Capability permanently deleted");
      loadCapabilities();
    } catch (error) {
      toast.error("Failed to permanently delete capability");
      console.error(error);
    }
  };

  const loadBlockingRecommendations = async (capabilityId: string) => {
    setLoadingRecommendations(true);
    try {
      const response = await apiClient.getCapabilityRecommendations(capabilityId);
      setBlockingRecommendations(response.results);
    } catch (error) {
      console.error("Failed to load blocking recommendations:", error);
      setBlockingRecommendations([]);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const handleDeleteRecommendation = async (recommendationId: string) => {
    try {
      const result = await apiClient.permanentDeleteRecommendation(recommendationId);
      toast.success(result.message || "Recommendation deleted");
      // Reload the blocking recommendations
      if (blockingRecommendations.length > 0) {
        const capabilityId = blockingRecommendations[0].target_capability;
        if (capabilityId) {
          await loadBlockingRecommendations(capabilityId);
        }
      }
    } catch (error) {
      toast.error("Failed to delete recommendation");
      console.error(error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      parent: null,
      status: "CURRENT",
      strategic_importance: "MEDIUM",
      owner: "",
      notes: ""
    });
    setSelectedCapability(null);
  };

  const openEditDialog = (capability: Capability) => {
    setSelectedCapability(capability);
    setFormData({
      name: capability.name,
      description: capability.description,
      parent: capability.parent,
      status: capability.status,
      strategic_importance: capability.strategic_importance,
      owner: capability.owner || "",
      notes: capability.notes || ""
    });
    setIsEditDialogOpen(true);
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case "CRITICAL": return "text-red-600 bg-red-50";
      case "HIGH": return "text-orange-600 bg-orange-50";
      case "MEDIUM": return "text-yellow-600 bg-yellow-50";
      case "LOW": return "text-green-600 bg-green-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "CURRENT": return "text-green-600 bg-green-50";
      case "PROPOSED": return "text-blue-600 bg-blue-50";
      case "DEPRECATED": return "text-orange-600 bg-orange-50";
      case "ARCHIVED": return "text-gray-600 bg-gray-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const rootCapabilities = filteredCapabilities.filter(cap => cap.level === 1);
  const childCapabilities = filteredCapabilities.filter(cap => cap.level > 1);

  if (loading) {
  return (
    <div className="space-y-4">
      <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <Progress value={33} className="w-48 mb-4" />
                <p className="text-muted-foreground">Loading capabilities...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Business Capability Map</h1>
          <p className="text-muted-foreground mt-1">
            Manage and visualize your organization's business capabilities
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="h-4 w-4 mr-2" />
              Add Capability
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Create New Capability</DialogTitle>
              <DialogDescription>
                Add a new business capability to your organization's map.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <label htmlFor="name" className="text-sm font-medium">Name</label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Customer Relationship Management"
                />
              </div>
              <div className="grid gap-2">
                <label htmlFor="description" className="text-sm font-medium">Description</label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Detailed description of the capability..."
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label htmlFor="parent" className="text-sm font-medium">Parent Capability</label>
                  <Select value={formData.parent || "none"} onValueChange={(value) => setFormData(prev => ({ ...prev, parent: value === "none" ? null : value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select parent (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None (Root Level)</SelectItem>
                      {capabilities.map((cap) => (
                        <SelectItem key={cap.id} value={cap.id}>
                          {cap.full_path}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <label htmlFor="importance" className="text-sm font-medium">Strategic Importance</label>
                  <Select value={formData.strategic_importance} onValueChange={(value: any) => setFormData(prev => ({ ...prev, strategic_importance: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CRITICAL">Critical</SelectItem>
                      <SelectItem value="HIGH">High</SelectItem>
                      <SelectItem value="MEDIUM">Medium</SelectItem>
                      <SelectItem value="LOW">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label htmlFor="status" className="text-sm font-medium">Status</label>
                  <Select value={formData.status} onValueChange={(value: any) => setFormData(prev => ({ ...prev, status: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CURRENT">Current</SelectItem>
                      <SelectItem value="PROPOSED">Proposed</SelectItem>
                      <SelectItem value="DEPRECATED">Deprecated</SelectItem>
                      <SelectItem value="ARCHIVED">Archived</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <label htmlFor="owner" className="text-sm font-medium">Owner</label>
                  <Input
                    id="owner"
                    value={formData.owner || ""}
                    onChange={(e) => setFormData(prev => ({ ...prev, owner: e.target.value }))}
                    placeholder="Team or person responsible"
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <label htmlFor="notes" className="text-sm font-medium">Notes</label>
                <Textarea
                  id="notes"
                  value={formData.notes || ""}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Additional notes (optional)"
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!formData.name || !formData.description}>
                Create Capability
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-6">
          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="basic">Basic Search</TabsTrigger>
              <TabsTrigger value="vector">AI Semantic Search</TabsTrigger>
            </TabsList>
            <TabsContent value="basic" className="space-y-4">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search capabilities..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="CURRENT">Current</SelectItem>
                    <SelectItem value="PROPOSED">Proposed</SelectItem>
                    <SelectItem value="DEPRECATED">Deprecated</SelectItem>
                    <SelectItem value="ARCHIVED">Archived</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={importanceFilter} onValueChange={setImportanceFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by importance" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Importance</SelectItem>
                    <SelectItem value="CRITICAL">Critical</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="MEDIUM">Medium</SelectItem>
                    <SelectItem value="LOW">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
            <TabsContent value="vector" className="space-y-4">
              <VectorSearchInput
                onSearch={handleVectorSearch}
                isLoading={searchLoading}
                placeholder="Find similar capabilities using AI..."
              />
              {searchResults.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground">
                    AI Search Results ({searchResults.length})
                  </h4>
                  <div className="grid gap-2">
                    {searchResults.map((result) => (
                      <Card key={result.id} className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h5 className="font-medium">{result.name}</h5>
                            <p className="text-sm text-muted-foreground line-clamp-1">
                              {result.description}
                            </p>
                            {result.full_path && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {result.full_path}
                              </p>
                            )}
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-sm font-medium">
                              {Math.round(result.similarity_score * 100)}% match
                            </div>
                            <Progress 
                              value={result.similarity_score * 100} 
                              className="w-16 h-2 mt-1" 
                            />
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
          </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Hierarchical Capability Tree */}
      <div className="space-y-4">
        {filteredCapabilities.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-muted-foreground">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No capabilities found</h3>
                <p className="mb-4">
                  {capabilities.length === 0 
                    ? "Start by creating your first business capability."
                    : "Try adjusting your search or filters."
                  }
                </p>
                {capabilities.length === 0 && (
                  <Button onClick={() => setIsCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create First Capability
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Business Capability Hierarchy ({filteredCapabilities.length} capabilities)
            </h2>
            <HierarchicalCapabilityTree
              capabilities={filteredCapabilities}
              onEdit={openEditDialog}
              onDelete={handleDelete}
              onPermanentDelete={handlePermanentDelete}
              onLoadBlockingRecommendations={loadBlockingRecommendations}
              onDeleteRecommendation={handleDeleteRecommendation}
              blockingRecommendations={blockingRecommendations}
              loadingRecommendations={loadingRecommendations}
              getImportanceColor={getImportanceColor}
              getStatusColor={getStatusColor}
            />
          </div>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Edit Capability</DialogTitle>
            <DialogDescription>
              Update the details of this business capability.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="edit-name" className="text-sm font-medium">Name</label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Customer Relationship Management"
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="edit-description" className="text-sm font-medium">Description</label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Detailed description of the capability..."
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <label htmlFor="edit-parent" className="text-sm font-medium">Parent Capability</label>
                <Select value={formData.parent || "none"} onValueChange={(value) => setFormData(prev => ({ ...prev, parent: value === "none" ? null : value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None (Root Level)</SelectItem>
                    {capabilities.filter(cap => cap.id !== selectedCapability?.id).map((cap) => (
                      <SelectItem key={cap.id} value={cap.id}>
                        {cap.full_path}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <label htmlFor="edit-importance" className="text-sm font-medium">Strategic Importance</label>
                <Select value={formData.strategic_importance} onValueChange={(value: any) => setFormData(prev => ({ ...prev, strategic_importance: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CRITICAL">Critical</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="MEDIUM">Medium</SelectItem>
                    <SelectItem value="LOW">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <label htmlFor="edit-status" className="text-sm font-medium">Status</label>
                <Select value={formData.status} onValueChange={(value: any) => setFormData(prev => ({ ...prev, status: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CURRENT">Current</SelectItem>
                    <SelectItem value="PROPOSED">Proposed</SelectItem>
                    <SelectItem value="DEPRECATED">Deprecated</SelectItem>
                    <SelectItem value="ARCHIVED">Archived</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <label htmlFor="edit-owner" className="text-sm font-medium">Owner</label>
                <Input
                  id="edit-owner"
                  value={formData.owner || ""}
                  onChange={(e) => setFormData(prev => ({ ...prev, owner: e.target.value }))}
                  placeholder="Team or person responsible"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <label htmlFor="edit-notes" className="text-sm font-medium">Notes</label>
              <Textarea
                id="edit-notes"
                value={formData.notes || ""}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Additional notes (optional)"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} disabled={!formData.name || !formData.description}>
              Update Capability
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface CapabilityCardProps {
  capability: Capability;
  onEdit: (capability: Capability) => void;
  onDelete: (capability: Capability) => void;
  onPermanentDelete: (capability: Capability) => void;
  onLoadBlockingRecommendations: (capabilityId: string) => void;
  onDeleteRecommendation: (recommendationId: string) => void;
  blockingRecommendations: CapabilityRecommendation[];
  loadingRecommendations: boolean;
  getImportanceColor: (importance: string) => string;
  getStatusColor: (status: string) => string;
}

function CapabilityCard({ capability, onEdit, onDelete, onPermanentDelete, onLoadBlockingRecommendations, onDeleteRecommendation, blockingRecommendations, loadingRecommendations, getImportanceColor, getStatusColor }: CapabilityCardProps) {
  const hasChildren = (capability.children_count || 0) > 0;
  const childrenCount = capability.children_count || 0;

  // Check if this capability has blocking recommendations
  const capabilityBlockingRecs = blockingRecommendations.filter(
    (rec: CapabilityRecommendation) => rec.target_capability === capability.id
  );

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg leading-tight">{capability.name}</CardTitle>
            {capability.full_path !== capability.name && (
              <p className="text-xs text-muted-foreground mt-1">{capability.full_path}</p>
            )}
          </div>
          <div className="flex gap-1 ml-2">
            <Button variant="ghost" size="sm" onClick={() => onEdit(capability)}>
              <Edit className="h-4 w-4" />
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="hover:bg-red-50"
                  onClick={() => onLoadBlockingRecommendations(capability.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Capability</AlertDialogTitle>
                  <AlertDialogDescription>
                    Choose how you want to delete "{capability.name}":
                  </AlertDialogDescription>
                  {hasChildren && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                      <strong>Warning:</strong> This capability has {childrenCount} sub-capabilities that will need to be reassigned before permanent deletion.
                    </div>
                  )}
                  {capabilityBlockingRecs.length > 0 && (
                    <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                      <h4 className="font-medium text-red-900 mb-2">
                        ⚠️ Blocking Recommendations ({capabilityBlockingRecs.length})
                      </h4>
                      <p className="text-sm text-red-700 mb-3">
                        This capability cannot be permanently deleted because it's referenced by the following recommendations:
                      </p>
                      {loadingRecommendations ? (
                        <div className="text-sm text-gray-600">Loading recommendations...</div>
                      ) : (
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {capabilityBlockingRecs.map((rec: CapabilityRecommendation) => (
                            <div key={rec.id} className="flex items-center justify-between p-2 bg-white border border-red-200 rounded">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm text-red-900">
                                  {rec.recommendation_type.replace('_', ' ')}
                                </div>
                                <div className="text-xs text-red-600 truncate">
                                  From: {rec.business_goal_title}
                                </div>
                                <div className="text-xs text-gray-600">
                                  Status: {rec.status}
                                </div>
                              </div>
                              <Button
                                size="sm"
                                variant="destructive"
                                className="ml-2"
                                onClick={() => onDeleteRecommendation(rec.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </AlertDialogHeader>
                <div className="space-y-3 py-4">
                  <div className="p-3 border border-orange-200 rounded-lg bg-orange-50">
                    <h4 className="font-medium text-orange-900 mb-1">Archive (Recommended)</h4>
                    <p className="text-sm text-orange-700 mb-3">
                      Sets status to archived. Can be restored later. Maintains audit trail.
                    </p>
                    <Button 
                      onClick={() => onDelete(capability)} 
                      variant="outline" 
                      className="w-full border-orange-300 text-orange-700 hover:bg-orange-100"
                    >
                      Archive Capability
                    </Button>
                  </div>
                  <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                    <h4 className="font-medium text-red-900 mb-1">Permanently Delete</h4>
                    <p className="text-sm text-red-700 mb-3">
                      Completely removes from database. This action cannot be undone.
                    </p>
                    <Button 
                      onClick={() => onPermanentDelete(capability)} 
                      variant="destructive" 
                      className="w-full"
                      disabled={hasChildren || capabilityBlockingRecs.length > 0}
                    >
                      {hasChildren 
                        ? "Cannot Delete (Has Children)" 
                        : capabilityBlockingRecs.length > 0
                        ? "Cannot Delete (Has Recommendations)"
                        : "Permanently Delete"}
                    </Button>
                  </div>
                </div>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
          {capability.description}
        </p>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Status</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(capability.status)}`}>
              {capability.status}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Importance</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImportanceColor(capability.strategic_importance)}`}>
              {capability.strategic_importance}
            </span>
          </div>
          {capability.owner && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Owner</span>
              <span className="text-xs font-medium">{capability.owner}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Level</span>
            <span className="text-xs font-medium">Level {capability.level}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface HierarchicalCapabilityTreeProps {
  capabilities: Capability[];
  onEdit: (capability: Capability) => void;
  onDelete: (capability: Capability) => void;
  onPermanentDelete: (capability: Capability) => void;
  onLoadBlockingRecommendations: (capabilityId: string) => void;
  onDeleteRecommendation: (recommendationId: string) => void;
  blockingRecommendations: CapabilityRecommendation[];
  loadingRecommendations: boolean;
  getImportanceColor: (importance: string) => string;
  getStatusColor: (status: string) => string;
}

function HierarchicalCapabilityTree({ 
  capabilities, 
  onEdit, 
  onDelete, 
  onPermanentDelete, 
  onLoadBlockingRecommendations,
  onDeleteRecommendation,
  blockingRecommendations,
  loadingRecommendations,
  getImportanceColor, 
  getStatusColor 
}: HierarchicalCapabilityTreeProps) {
  // Build capability hierarchy with proper typing
  const buildHierarchy = (caps: Capability[]): (Capability & { children: (Capability & { children: any[] })[] })[] => {
    const capMap = new Map<string, Capability & { children: (Capability & { children: any[] })[] }>();
    
    // Initialize all capabilities with empty children arrays
    caps.forEach(cap => {
      capMap.set(cap.id, { ...cap, children: [] });
    });
    
    // Build parent-child relationships
    const roots: (Capability & { children: (Capability & { children: any[] })[] })[] = [];
    caps.forEach(cap => {
      const capWithChildren = capMap.get(cap.id)!;
      if (cap.parent) {
        const parent = capMap.get(cap.parent);
        if (parent) {
          parent.children.push(capWithChildren);
        } else {
          // Parent not in filtered list, treat as root
          roots.push(capWithChildren);
        }
      } else {
        roots.push(capWithChildren);
      }
    });
    
    return roots;
  };

  const hierarchicalCapabilities = buildHierarchy(capabilities);

  return (
    <div className="space-y-4">
      {hierarchicalCapabilities.map(capability => (
        <CapabilityTreeNode
          key={capability.id}
          capability={capability}
          level={0}
          onEdit={onEdit}
          onDelete={onDelete}
          onPermanentDelete={onPermanentDelete}
          onLoadBlockingRecommendations={onLoadBlockingRecommendations}
          onDeleteRecommendation={onDeleteRecommendation}
          blockingRecommendations={blockingRecommendations}
          loadingRecommendations={loadingRecommendations}
          getImportanceColor={getImportanceColor}
          getStatusColor={getStatusColor}
        />
      ))}
    </div>
  );
}

interface CapabilityTreeNodeProps {
  capability: Capability & { children: (Capability & { children: any[] })[] };
  level: number;
  onEdit: (capability: Capability) => void;
  onDelete: (capability: Capability) => void;
  onPermanentDelete: (capability: Capability) => void;
  onLoadBlockingRecommendations: (capabilityId: string) => void;
  onDeleteRecommendation: (recommendationId: string) => void;
  blockingRecommendations: CapabilityRecommendation[];
  loadingRecommendations: boolean;
  getImportanceColor: (importance: string) => string;
  getStatusColor: (status: string) => string;
}

function CapabilityTreeNode({
  capability,
  level,
  onEdit,
  onDelete,
  onPermanentDelete,
  onLoadBlockingRecommendations,
  onDeleteRecommendation,
  blockingRecommendations,
  loadingRecommendations,
  getImportanceColor,
  getStatusColor
}: CapabilityTreeNodeProps) {
  const [expanded, setExpanded] = React.useState(false);
  const hasChildren = capability.children.length > 0;

  // Calculate indentation based on level
  const getIndentationClass = (level: number) => {
    if (level === 0) return '';
    
    const borderColors = [
      'border-blue-200',
      'border-green-200', 
      'border-purple-200',
      'border-orange-200',
      'border-pink-200',
      'border-indigo-200'
    ];
    
    const borderColor = borderColors[(level - 1) % borderColors.length];
    
    return `pl-4 border-l-2 ${borderColor}`;
  };

  const getIndentationStyle = (level: number) => {
    if (level === 0) return {};
    return { marginLeft: `${level * 24}px` }; // 24px, 48px, 72px, 96px...
  };

  return (
    <div className="space-y-3">
      <div className={level > 0 ? getIndentationClass(level) : ''} style={getIndentationStyle(level)}>
        <CapabilityTreeCard
          capability={capability}
          level={level}
          expanded={expanded}
          hasChildren={hasChildren}
          onToggleExpanded={() => setExpanded(!expanded)}
          onEdit={onEdit}
          onDelete={onDelete}
          onPermanentDelete={onPermanentDelete}
          onLoadBlockingRecommendations={onLoadBlockingRecommendations}
          onDeleteRecommendation={onDeleteRecommendation}
          blockingRecommendations={blockingRecommendations}
          loadingRecommendations={loadingRecommendations}
          getImportanceColor={getImportanceColor}
          getStatusColor={getStatusColor}
        />
      </div>
      {hasChildren && expanded && (
        <div className="space-y-3">
          {capability.children.map(child => (
            <CapabilityTreeNode
              key={child.id}
              capability={child as Capability & { children: (Capability & { children: any[] })[] }}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              onPermanentDelete={onPermanentDelete}
              onLoadBlockingRecommendations={onLoadBlockingRecommendations}
              onDeleteRecommendation={onDeleteRecommendation}
              blockingRecommendations={blockingRecommendations}
              loadingRecommendations={loadingRecommendations}
              getImportanceColor={getImportanceColor}
              getStatusColor={getStatusColor}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CapabilityTreeCardProps {
  capability: Capability & { children?: any[] };
  level: number;
  expanded: boolean;
  hasChildren: boolean;
  onToggleExpanded: () => void;
  onEdit: (capability: Capability) => void;
  onDelete: (capability: Capability) => void;
  onPermanentDelete: (capability: Capability) => void;
  onLoadBlockingRecommendations: (capabilityId: string) => void;
  onDeleteRecommendation: (recommendationId: string) => void;
  blockingRecommendations: CapabilityRecommendation[];
  loadingRecommendations: boolean;
  getImportanceColor: (importance: string) => string;
  getStatusColor: (status: string) => string;
}

function CapabilityTreeCard({ 
  capability, 
  level, 
  expanded,
  hasChildren,
  onToggleExpanded,
  onEdit, 
  onDelete, 
  onPermanentDelete, 
  onLoadBlockingRecommendations,
  onDeleteRecommendation,
  blockingRecommendations,
  loadingRecommendations,
  getImportanceColor, 
  getStatusColor 
}: CapabilityTreeCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  
  // Get styling based on level
  const getCardStyling = (level: number) => {
    switch (level) {
      case 0:
        return {
          cardClass: "border-2 border-primary/30 shadow-lg",
          titleClass: "text-xl font-bold text-primary",
          levelBadge: "bg-primary text-primary-foreground"
        };
      case 1:
        return {
          cardClass: "border-l-4 border-l-blue-400 shadow-md bg-blue-50/50",
          titleClass: "text-lg font-semibold text-blue-900",
          levelBadge: "bg-blue-500 text-white"
        };
      case 2:
        return {
          cardClass: "border-l-4 border-l-green-400 shadow-sm bg-green-50/30",
          titleClass: "text-base font-medium text-green-800",
          levelBadge: "bg-green-500 text-white"
        };
      case 3:
        return {
          cardClass: "border-l-4 border-l-purple-400 bg-purple-50/20",
          titleClass: "text-sm font-medium text-purple-800",
          levelBadge: "bg-purple-500 text-white"
        };
      default:
        return {
          cardClass: "border-l-4 border-l-gray-400 bg-gray-50/20",
          titleClass: "text-sm font-medium text-gray-800",
          levelBadge: "bg-gray-500 text-white"
        };
    }
  };

  const styling = getCardStyling(level);
  const childrenCount = capability.children?.length || 0;
  
  // Check if this capability has blocking recommendations
  const capabilityBlockingRecs = blockingRecommendations.filter(
    rec => rec.target_capability === capability.id
  );
  const hasBlockingRecommendations = capabilityBlockingRecs.length > 0;

  const handleDeleteClick = () => {
    setShowDeleteDialog(true);
    // Load blocking recommendations when delete dialog opens
    onLoadBlockingRecommendations(capability.id);
  };

  const handlePermanentDeleteAttempt = async () => {
    // Reload recommendations to check current state
    await onLoadBlockingRecommendations(capability.id);
    
    // Check if there are still blocking recommendations
    const currentBlockingRecs = blockingRecommendations.filter(
      rec => rec.target_capability === capability.id
    );
    
    if (currentBlockingRecs.length === 0) {
      onPermanentDelete(capability);
      setShowDeleteDialog(false);
    }
  };

  return (
    <Card className={`transition-all duration-200 ${styling.cardClass}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {hasChildren && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleExpanded}
                className="p-0 h-6 w-6 mt-1 hover:bg-primary/10 transition-transform duration-200"
                style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)' }}
              >
                <ChevronDown className="h-4 w-4" />
              </Button>
            )}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <CardTitle className={`${styling.titleClass} leading-tight`}>
                  {capability.name}
                </CardTitle>
                <span className={`text-xs px-2 py-1 rounded font-medium ${styling.levelBadge}`}>
                  L{capability.level}
                </span>
                {hasChildren && (
                  <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded border">
                    {childrenCount} sub-{childrenCount === 1 ? 'capability' : 'capabilities'}
                  </span>
                )}

              </div>
              <p className={`text-sm text-muted-foreground mb-3 ${level > 2 ? 'line-clamp-1' : 'line-clamp-2'}`}>
                {capability.description}
              </p>
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(capability.status)}`}>
                  {capability.status}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImportanceColor(capability.strategic_importance)}`}>
                  {capability.strategic_importance}
                </span>
                {capability.owner && (
                  <span className="text-xs text-muted-foreground">
                    👤 {capability.owner}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-1 ml-2">
            <Button variant="ghost" size="sm" onClick={() => onEdit(capability)} className="hover:bg-primary/10">
              <Edit className="h-4 w-4" />
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="hover:bg-red-50"
                  onClick={() => onLoadBlockingRecommendations(capability.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Capability</AlertDialogTitle>
                  <AlertDialogDescription>
                    Choose how you want to delete "{capability.name}":
                  </AlertDialogDescription>
                  {hasChildren && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                      <strong>Warning:</strong> This capability has {childrenCount} sub-capabilities that will need to be reassigned before permanent deletion.
                    </div>
                  )}
                  {capabilityBlockingRecs.length > 0 && (
                    <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                      <h4 className="font-medium text-red-900 mb-2">
                        ⚠️ Blocking Recommendations ({capabilityBlockingRecs.length})
                      </h4>
                      <p className="text-sm text-red-700 mb-3">
                        This capability cannot be permanently deleted because it's referenced by the following recommendations:
                      </p>
                      {loadingRecommendations ? (
                        <div className="text-sm text-gray-600">Loading recommendations...</div>
                      ) : (
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {capabilityBlockingRecs.map((rec: CapabilityRecommendation) => (
                            <div key={rec.id} className="flex items-center justify-between p-2 bg-white border border-red-200 rounded">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm text-red-900">
                                  {rec.recommendation_type.replace('_', ' ')}
                                </div>
                                <div className="text-xs text-red-600 truncate">
                                  From: {rec.business_goal_title}
                                </div>
                                <div className="text-xs text-gray-600">
                                  Status: {rec.status}
                                </div>
                              </div>
                              <Button
                                size="sm"
                                variant="destructive"
                                className="ml-2"
                                onClick={() => onDeleteRecommendation(rec.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </AlertDialogHeader>
                <div className="space-y-3 py-4">
                  <div className="p-3 border border-orange-200 rounded-lg bg-orange-50">
                    <h4 className="font-medium text-orange-900 mb-1">Archive (Recommended)</h4>
                    <p className="text-sm text-orange-700 mb-3">
                      Sets status to archived. Can be restored later. Maintains audit trail.
                    </p>
                    <Button 
                      onClick={handleDeleteClick} 
                      variant="outline" 
                      className="w-full border-orange-300 text-orange-700 hover:bg-orange-100"
                    >
                      Archive Capability
                    </Button>
                  </div>
                  <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                    <h4 className="font-medium text-red-900 mb-1">Permanently Delete</h4>
                    <p className="text-sm text-red-700 mb-3">
                      Completely removes from database. This action cannot be undone.
                    </p>
                    <Button 
                      onClick={handlePermanentDeleteAttempt} 
                      variant="destructive" 
                      className="w-full"
                      disabled={hasChildren || capabilityBlockingRecs.length > 0}
                    >
                      {hasChildren 
                        ? "Cannot Delete (Has Children)" 
                        : capabilityBlockingRecs.length > 0
                        ? "Cannot Delete (Has Recommendations)"
                        : "Permanently Delete"}
                    </Button>
                  </div>
                </div>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
} 