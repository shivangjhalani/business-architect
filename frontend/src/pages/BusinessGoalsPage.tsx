import * as React from "react";
import { Plus, Upload, FileText, Brain, Clock, CheckCircle, AlertCircle, Trash2, Edit } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VectorSearchInput } from "@/components/ui/vector-search-input";
import { apiClient, type BusinessGoal, type VectorSearchResult, type CapabilityRecommendation } from "@/lib/api";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

export function BusinessGoalsPage() {
  const [goals, setGoals] = React.useState<BusinessGoal[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = React.useState(false);
  const [searchResults, setSearchResults] = React.useState<VectorSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = React.useState(false);
  const [analyzingGoal, setAnalyzingGoal] = React.useState<string | null>(null);
  const [blockingRecommendations, setBlockingRecommendations] = React.useState<CapabilityRecommendation[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = React.useState(false);

  // Form state
  const [formData, setFormData] = React.useState({
    title: "",
    description: "",
    pdfFile: null as File | null
  });

  React.useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await apiClient.getBusinessGoals();
      setGoals(response.results);
    } catch (error) {
      toast.error("Failed to load business goals");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('title', formData.title);
      formDataToSend.append('description', formData.description);
      if (formData.pdfFile) {
        formDataToSend.append('pdf_file', formData.pdfFile);
      }

      await apiClient.createBusinessGoal(formDataToSend);
      toast.success("Business goal created successfully");
      setIsCreateDialogOpen(false);
      resetForm();
      loadGoals();
    } catch (error) {
      toast.error("Failed to create business goal");
      console.error(error);
    }
  };

  const handleAnalyze = async (goalId: string) => {
    setAnalyzingGoal(goalId);
    try {
      const response = await apiClient.analyzeBusinessGoal(goalId);
      toast.success(`Analysis complete! Created ${response.recommendations_created} recommendations`);
      loadGoals();
    } catch (error) {
      toast.error("Failed to analyze business goal");
      console.error(error);
    } finally {
      setAnalyzingGoal(null);
    }
  };

  const handleDelete = async (goal: BusinessGoal) => {
    try {
      await apiClient.deleteBusinessGoal(goal.id);
      toast.success("Business goal archived successfully");
      loadGoals();
    } catch (error) {
      toast.error("Failed to archive business goal");
      console.error(error);
    }
  };

  const handlePermanentDelete = async (goal: BusinessGoal) => {
    try {
      const result = await apiClient.permanentDeleteBusinessGoal(goal.id);
      toast.success(result.message || "Business goal permanently deleted");
      loadGoals();
    } catch (error) {
      toast.error("Failed to permanently delete business goal");
      console.error(error);
    }
  };

  const loadBlockingRecommendations = async (goalId: string) => {
    setLoadingRecommendations(true);
    try {
      const response = await apiClient.getBusinessGoalRecommendations(goalId);
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
      // Reload the blocking recommendations if we're currently viewing them
      if (blockingRecommendations.length > 0) {
        const goalId = blockingRecommendations[0].business_goal;
        await loadBlockingRecommendations(goalId);
      }
    } catch (error) {
      toast.error("Failed to delete recommendation");
      console.error(error);
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      pdfFile: null
    });
    setSearchResults([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === 'application/pdf') {
        setFormData(prev => ({ ...prev, pdfFile: file }));
        toast.success("PDF file attached");
      } else {
        toast.error("Please select a PDF file");
      }
    }
  };

  const handleSmartSearch = async (query: string) => {
    setSearchLoading(true);
    try {
      const response = await apiClient.searchBusinessGoals({ 
        query, 
        limit: 5, 
        threshold: 0.6 
      });
      setSearchResults(response.results);
      if (response.results.length > 0) {
        toast.success(`Found ${response.results.length} similar goals`);
      } else {
        toast.info("No similar goals found - this appears to be a unique objective");
      }
    } catch (error) {
      toast.error("Smart search failed");
      console.error(error);
    } finally {
      setSearchLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "PENDING_ANALYSIS":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case "ANALYZED":
        return <Brain className="h-4 w-4 text-blue-600" />;
      case "RECOMMENDATIONS_APPLIED":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "CLOSED":
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING_ANALYSIS": return "text-yellow-600 bg-yellow-50";
      case "ANALYZED": return "text-blue-600 bg-blue-50";
      case "RECOMMENDATIONS_APPLIED": return "text-green-600 bg-green-50";
      case "CLOSED": return "text-gray-600 bg-gray-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
  return (
    <div className="space-y-4">
      <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <Progress value={33} className="w-48 mb-4" />
                <p className="text-muted-foreground">Loading business goals...</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Business Goals</h1>
          <p className="text-muted-foreground mt-1">
            Submit strategic objectives for AI-powered capability analysis
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="h-4 w-4 mr-2" />
              Submit New Goal
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[700px]">
            <DialogHeader>
              <DialogTitle>Submit Business Goal</DialogTitle>
              <DialogDescription>
                Describe your strategic objective. Our AI will analyze it against your current capability map and suggest improvements.
              </DialogDescription>
            </DialogHeader>
            <Tabs defaultValue="details" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="details">Goal Details</TabsTrigger>
                <TabsTrigger value="smart-insights">Smart Insights</TabsTrigger>
              </TabsList>
              
              <TabsContent value="details" className="space-y-4">
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <label htmlFor="title" className="text-sm font-medium">Goal Title</label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="e.g., Digital Transformation Initiative"
                    />
                  </div>
                  <div className="grid gap-2">
                    <label htmlFor="description" className="text-sm font-medium">Description</label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Describe your business goal in detail. Include objectives, expected outcomes, and any constraints..."
                      rows={5}
                    />
                  </div>
                  <div className="grid gap-2">
                    <label htmlFor="pdf" className="text-sm font-medium">Supporting Document (Optional)</label>
                    <div className="flex items-center gap-4">
                      <Input
                        id="pdf"
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => document.getElementById('pdf')?.click()}
                        className="flex-1"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        {formData.pdfFile ? formData.pdfFile.name : "Upload PDF Document"}
                      </Button>
                      {formData.pdfFile && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setFormData(prev => ({ ...prev, pdfFile: null }))}
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Upload a PDF with additional details, requirements, or business case documentation
                    </p>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="smart-insights" className="space-y-4">
                <div className="py-4">
                  <VectorSearchInput
                    placeholder="Search for similar past goals to get insights..."
                    onSearch={handleSmartSearch}
                    isLoading={searchLoading}
                  />
                  
                  {searchResults.length > 0 && (
                    <div className="mt-6 space-y-3">
                      <h4 className="text-sm font-medium">Similar Past Goals</h4>
                      <div className="space-y-2">
                        {searchResults.map((result) => (
                          <Card key={result.id} className="p-3">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <h5 className="font-medium text-sm">{result.title}</h5>
                                <span className="text-xs text-muted-foreground">
                                  {Math.round(result.similarity_score * 100)}% similar
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground line-clamp-2">
                                {result.description}
                              </p>
                            </div>
                          </Card>
                        ))}
                      </div>
                      <div className="text-xs text-muted-foreground bg-blue-50 p-3 rounded-lg">
                        💡 <strong>Tip:</strong> Review these similar goals to refine your objective or learn from past approaches.
                      </div>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!formData.title || !formData.description}>
                Submit Goal
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Goals List */}
      <div className="grid gap-4">
        {goals.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No business goals yet</h3>
                <p className="mb-4">
                  Submit your first strategic objective to get AI-powered capability recommendations.
                </p>
                <Button onClick={() => setIsCreateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Submit First Goal
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onAnalyze={handleAnalyze}
              onDelete={handleDelete}
              onPermanentDelete={handlePermanentDelete}
              onLoadBlockingRecommendations={loadBlockingRecommendations}
              onDeleteRecommendation={handleDeleteRecommendation}
              blockingRecommendations={blockingRecommendations}
              loadingRecommendations={loadingRecommendations}
              analyzingGoal={analyzingGoal}
              getStatusIcon={getStatusIcon}
              getStatusColor={getStatusColor}
              formatDate={formatDate}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface GoalCardProps {
  goal: BusinessGoal;
  onAnalyze: (goalId: string) => void;
  onDelete: (goal: BusinessGoal) => void;
  onPermanentDelete: (goal: BusinessGoal) => void;
  onLoadBlockingRecommendations: (goalId: string) => void;
  onDeleteRecommendation: (recommendationId: string) => void;
  blockingRecommendations: CapabilityRecommendation[];
  loadingRecommendations: boolean;
  analyzingGoal: string | null;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusColor: (status: string) => string;
  formatDate: (date: string) => string;
}

function GoalCard({ 
  goal, 
  onAnalyze, 
  onDelete, 
  onPermanentDelete, 
  onLoadBlockingRecommendations, 
  onDeleteRecommendation, 
  blockingRecommendations, 
  loadingRecommendations, 
  analyzingGoal, 
  getStatusIcon, 
  getStatusColor, 
  formatDate 
}: GoalCardProps) {
  const [showDetails, setShowDetails] = React.useState(false);
  const navigate = useNavigate();

  // Check if this goal has blocking recommendations
  const goalBlockingRecs = blockingRecommendations.filter(
    (rec: CapabilityRecommendation) => rec.business_goal === goal.id
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <CardTitle className="text-xl">{goal.title}</CardTitle>
              {goal.pdf_filename && (
                <FileText className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                {getStatusIcon(goal.status)}
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(goal.status)}`}>
                  {goal.status.replace('_', ' ')}
                </span>
              </div>
              <span>Submitted {formatDate(goal.submitted_at)}</span>
              {goal.is_analyzed && (
                <span className="text-blue-600">
                  {goal.recommendations_count} recommendations • {goal.pending_recommendations_count} pending
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? "Hide" : "Show"} Details
            </Button>
            {goal.status === "PENDING_ANALYSIS" && (
              <Button
                size="sm"
                onClick={() => onAnalyze(goal.id)}
                disabled={analyzingGoal === goal.id}
              >
                {analyzingGoal === goal.id ? (
                  <>
                    <Brain className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" />
                    Analyze with AI
                  </>
                )}
              </Button>
            )}
            {goal.is_analyzed && (
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => navigate(`/analysis/${goal.id}`)}
              >
                View Recommendations
              </Button>
            )}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="hover:bg-red-50"
                  onClick={() => onLoadBlockingRecommendations(goal.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Business Goal</AlertDialogTitle>
                  <AlertDialogDescription>
                    Choose how you want to delete "{goal.title}":
                  </AlertDialogDescription>
                  {goalBlockingRecs.length > 0 && (
                    <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                      <h4 className="font-medium text-red-900 mb-2">
                        ⚠️ Blocking Recommendations ({goalBlockingRecs.length})
                      </h4>
                      <p className="text-sm text-red-700 mb-3">
                        This business goal cannot be permanently deleted because it has the following recommendations:
                      </p>
                      {loadingRecommendations ? (
                        <div className="text-sm text-gray-600">Loading recommendations...</div>
                      ) : (
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {goalBlockingRecs.map((rec: CapabilityRecommendation) => (
                            <div key={rec.id} className="flex items-center justify-between p-2 bg-white border border-red-200 rounded">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm text-red-900">
                                  {rec.recommendation_type.replace('_', ' ')}
                                </div>
                                <div className="text-xs text-red-600 truncate">
                                  Target: {rec.proposed_name || rec.target_capability || 'N/A'}
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
                      Sets status to closed. Can be restored later. Maintains audit trail.
                    </p>
                    <Button 
                      onClick={() => onDelete(goal)} 
                      variant="outline" 
                      className="w-full border-orange-300 text-orange-700 hover:bg-orange-100"
                    >
                      Archive Business Goal
                    </Button>
                  </div>
                  <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                    <h4 className="font-medium text-red-900 mb-1">Permanently Delete</h4>
                    <p className="text-sm text-red-700 mb-3">
                      Completely removes from database. This action cannot be undone.
                    </p>
                    <Button 
                      onClick={() => onPermanentDelete(goal)} 
                      variant="destructive" 
                      className="w-full"
                      disabled={goalBlockingRecs.length > 0}
                    >
                      {goalBlockingRecs.length > 0
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

      {showDetails && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium mb-2">Description</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {goal.description}
              </p>
            </div>

            {goal.pdf_filename && (
              <div>
                <h4 className="text-sm font-medium mb-2">Attached Document</h4>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span>{goal.pdf_filename}</span>
                </div>
              </div>
            )}

            {analyzingGoal === goal.id && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="h-4 w-4 text-blue-600 animate-pulse" />
                  <span className="text-sm font-medium text-blue-900">AI Analysis in Progress</span>
                </div>
                <p className="text-xs text-blue-700 mb-3">
                  Analyzing your goal against the current capability map and finding optimization opportunities...
                </p>
                <Progress value={75} className="h-2" />
              </div>
            )}
          </div>
        </CardContent>
      )}
      </Card>
  );
} 