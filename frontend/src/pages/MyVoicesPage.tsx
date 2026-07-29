import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, Mic, Clock, AudioLines, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface VoiceProfile {
  id: string;
  name: string;
  type: "reference" | "recorded";
  duration_sec: number;
  recordings_count: number;
  created_at: string;
}

export default function MyVoicesPage() {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadRefText, setUploadRefText] = useState("");
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const fetchVoices = () => {
    fetch("/api/voices/")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setVoices(data);
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchVoices();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this voice?")) return;
    await fetch(`/api/voices/${id}`, { method: "DELETE" });
    fetchVoices();
  };

  const handleUploadVoice = async () => {
    if (!uploadFile || !uploadName.trim()) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("name", uploadName);
      formData.append("audio", uploadFile);
      formData.append("reference_text", uploadRefText);

      const res = await fetch("/api/voices/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      setShowUpload(false);
      setUploadName("");
      setUploadFile(null);
      setUploadRefText("");
      fetchVoices();
    } catch {
      alert("Failed to create voice profile.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Voices</h1>
          <p className="text-muted-foreground mt-1">Manage your saved voice profiles</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowUpload(!showUpload)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Voice
          </Button>
          <Button onClick={() => navigate("/record")}>
            <Plus className="h-4 w-4 mr-2" />
            Record New Voice
          </Button>
        </div>
      </div>

      {/* Upload form */}
      {showUpload && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Create Voice from Audio</CardTitle>
            <CardDescription>Upload 10-30 seconds of audio to create a voice profile</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="Voice name (e.g. My Voice, Narrator...)"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
            />
            <div className="flex gap-3">
              <label className="cursor-pointer flex-1">
                <div className="border-2 border-dashed rounded-md p-4 text-center hover:bg-accent transition-colors">
                  {uploadFile ? (
                    <span className="text-sm">{uploadFile.name}</span>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      Click to select audio file
                    </span>
                  )}
                </div>
                <input
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>
            <Input
              placeholder="Reference text (optional — what the audio says)"
              value={uploadRefText}
              onChange={(e) => setUploadRefText(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowUpload(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleUploadVoice}
                disabled={!uploadFile || !uploadName.trim() || uploading}
              >
                {uploading ? "Creating..." : "Create Voice"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Voice list */}
      {voices.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <AudioLines className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="font-semibold text-lg">No voices yet</h3>
            <p className="text-muted-foreground mt-1">
              Upload a reference audio or record sentences to create your first voice
            </p>
            <div className="flex justify-center gap-3 mt-4">
              <Button variant="outline" onClick={() => setShowUpload(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Upload Audio
              </Button>
              <Button onClick={() => navigate("/record")}>
                <Mic className="h-4 w-4 mr-2" />
                Start Recording
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {voices.map((v) => (
            <Card key={v.id} className="group">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    {v.type === "recorded" ? (
                      <Mic className="h-5 w-5 text-primary" />
                    ) : (
                      <AudioLines className="h-5 w-5 text-primary" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold">{v.name}</h3>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {v.duration_sec}s
                      </span>
                      {v.type === "recorded" && (
                        <span>{v.recordings_count} recordings</span>
                      )}
                      <span>
                        {v.type === "reference" ? "Uploaded" : "Recorded"}
                      </span>
                      <span>
                        {new Date(v.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/clone?voice=${v.id}`)}
                  >
                    Use Voice
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => handleDelete(v.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
