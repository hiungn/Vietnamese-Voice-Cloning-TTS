import { useState, useRef, useEffect } from "react";
import { Upload, Mic, Square, Trash2, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { AudioPlayer } from "@/components/AudioPlayer";

interface VoiceProfile {
  id: string;
  name: string;
}

export default function ClonePage() {
  // Reference audio
  const [refAudioFile, setRefAudioFile] = useState<File | null>(null);
  const [refPreviewUrl, setRefPreviewUrl] = useState<string | null>(null);
  const [refText, setRefText] = useState("");

  // Recording
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Text input
  const [text, setText] = useState("");

  // Output
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Saved voices
  const [savedVoices, setSavedVoices] = useState<VoiceProfile[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>("");
  const [mode, setMode] = useState<"upload" | "saved">("upload");

  useEffect(() => {
    fetch("/api/voices/")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setSavedVoices(data);
      })
      .catch(() => {});
  }, []);

  // --- Recording ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(blob);
        setRefPreviewUrl(url);
        setRefAudioFile(new File([blob], "recording.webm", { type: "audio/webm" }));
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const clearRef = () => {
    if (refPreviewUrl) URL.revokeObjectURL(refPreviewUrl);
    setRefPreviewUrl(null);
    setRefAudioFile(null);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setRefAudioFile(file);
    setRefPreviewUrl(URL.createObjectURL(file));
  };

  // --- Submit ---
  const handleClone = async () => {
    if (!text.trim()) return;

    setIsProcessing(true);
    setAudioUrl(null);

    try {
      if (mode === "saved" && selectedVoice) {
        // Clone with saved voice
        const formData = new FormData();
        formData.append("text", text);
        formData.append("voice_id", selectedVoice);
        formData.append("format", "wav");

        const res = await fetch("/api/clone/with-voice", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Clone failed");
        const blob = await res.blob();
        setAudioUrl(URL.createObjectURL(blob));
      } else {
        // Quick clone with uploaded/recorded audio
        if (!refAudioFile) return;

        const formData = new FormData();
        formData.append("text", text);
        formData.append("reference_audio", refAudioFile);
        formData.append("reference_text", refText);
        formData.append("format", "wav");

        const res = await fetch("/api/clone/quick", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Clone failed");
        const blob = await res.blob();
        setAudioUrl(URL.createObjectURL(blob));
      }
    } catch (err) {
      console.error(err);
      alert("Voice cloning failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const canSubmit =
    text.trim().length > 0 &&
    !isProcessing &&
    ((mode === "upload" && refAudioFile) || (mode === "saved" && selectedVoice));

  return (
    <div className="max-w-4xl mx-auto p-6 pb-24 space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Voice Clone</h1>
        <p className="text-muted-foreground mt-1">
          Clone any voice with just 10-30 seconds of audio
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        <Button
          variant={mode === "upload" ? "default" : "outline"}
          onClick={() => setMode("upload")}
          size="sm"
        >
          <Upload className="h-4 w-4 mr-2" />
          Upload / Record
        </Button>
        {savedVoices.length > 0 && (
          <Button
            variant={mode === "saved" ? "default" : "outline"}
            onClick={() => setMode("saved")}
            size="sm"
          >
            Saved Voices
          </Button>
        )}
      </div>

      {/* Reference Audio Section */}
      {mode === "upload" ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Reference Audio</CardTitle>
            <CardDescription>
              Upload or record 10-30 seconds of the voice you want to clone
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!refPreviewUrl ? (
              <div className="flex gap-3">
                {/* Upload button */}
                <label className="cursor-pointer">
                  <Button variant="outline" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Audio
                    </span>
                  </Button>
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>

                {/* Record button */}
                {!isRecording ? (
                  <Button variant="outline" onClick={startRecording}>
                    <Mic className="h-4 w-4 mr-2" />
                    Record
                  </Button>
                ) : (
                  <Button variant="destructive" onClick={stopRecording}>
                    <Square className="h-4 w-4 mr-2 fill-current" />
                    Stop Recording
                  </Button>
                )}

                {isRecording && (
                  <div className="flex items-center gap-2 text-destructive">
                    <div className="h-2 w-2 rounded-full bg-destructive animate-pulse-recording" />
                    <span className="text-sm font-medium">Recording...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <audio controls src={refPreviewUrl} className="flex-1 h-10" />
                <Button variant="ghost" size="icon" onClick={clearRef}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            )}

            {/* Reference text (optional) */}
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Reference text (optional — improves quality)
              </label>
              <Input
                value={refText}
                onChange={(e) => setRefText(e.target.value)}
                placeholder="Type what the reference audio says..."
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select a Saved Voice</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {savedVoices.map((v) => (
                <Button
                  key={v.id}
                  variant={selectedVoice === v.id ? "default" : "outline"}
                  onClick={() => setSelectedVoice(v.id)}
                  className="justify-start"
                >
                  {v.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Text Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Text to Speak</CardTitle>
          <CardDescription>Enter the text you want the cloned voice to say</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Nhap van ban muon chuyen thanh giong noi..."
            rows={6}
            className="resize-none"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {text.length} characters
            </span>
            <Button onClick={handleClone} disabled={!canSubmit} size="lg">
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Clone Voice
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audio Player */}
      {audioUrl && (
        <AudioPlayer
          src={audioUrl}
          filename="voice_clone.wav"
          onClose={() => setAudioUrl(null)}
        />
      )}
    </div>
  );
}
