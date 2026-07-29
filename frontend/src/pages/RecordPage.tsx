import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Mic,
  Square,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Check,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";

interface Script {
  text: string;
}

export default function RecordPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [index, setIndex] = useState(0);
  const [recordings, setRecordings] = useState<Record<number, string>>({});
  const [status, setStatus] = useState<"ready" | "countdown" | "recording">("ready");
  const [countdown, setCountdown] = useState(3);
  const [voiceId, setVoiceId] = useState<string>("");
  const [voiceName, setVoiceName] = useState("");
  const [showSave, setShowSave] = useState(false);
  const [saving, setSaving] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const navigate = useNavigate();

  // Load scripts and create session
  useEffect(() => {
    fetch("/api/recordings/scripts")
      .then((r) => r.json())
      .then((data) => setScripts(data.scripts || []));

    fetch("/api/recordings/new-session", { method: "POST" })
      .then((r) => r.json())
      .then((data) => setVoiceId(data.voice_id));
  }, []);

  // Load existing progress if resuming
  useEffect(() => {
    if (!voiceId) return;
    fetch(`/api/recordings/progress/${voiceId}`)
      .then((r) => r.json())
      .then((data) => {
        const recs: Record<number, string> = {};
        (data.recorded || []).forEach((i: number) => {
          recs[i] = "saved";
        });
        setRecordings(recs);
      })
      .catch(() => {});
  }, [voiceId]);

  const totalRecorded = Object.keys(recordings).length;
  const progress = scripts.length > 0 ? (totalRecorded / scripts.length) * 100 : 0;

  const goTo = (i: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIndex(Math.max(0, Math.min(scripts.length - 1, i)));
    setStatus("ready");
  };

  const startCountdown = () => {
    if (status !== "ready" || recordings[index]) return;
    setStatus("countdown");
    setCountdown(3);

    timerRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c > 1) return c - 1;
        if (timerRef.current) clearInterval(timerRef.current);
        startRecording();
        return 0;
      });
    }, 1000);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });

        // Upload to server
        const formData = new FormData();
        formData.append("voice_id", voiceId);
        formData.append("index", index.toString());
        formData.append("audio", new File([blob], `${index}.webm`, { type: "audio/webm" }));

        try {
          const res = await fetch("/api/recordings/save", {
            method: "POST",
            body: formData,
          });
          if (res.ok) {
            const url = URL.createObjectURL(blob);
            setRecordings((r) => ({ ...r, [index]: url }));
          }
        } catch {
          console.error("Failed to save recording");
        }

        setStatus("ready");
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setStatus("recording");
    } catch (err) {
      console.error("Microphone error:", err);
      setStatus("ready");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state !== "inactive") {
      mediaRecorderRef.current?.stop();
    }
    setStatus("ready");
  };

  const deleteRecording = async () => {
    await fetch(`/api/recordings/${voiceId}/${index}`, { method: "DELETE" });
    setRecordings((r) => {
      const copy = { ...r };
      delete copy[index];
      return copy;
    });
  };

  const handleSaveVoice = async () => {
    if (!voiceName.trim()) return;
    setSaving(true);

    try {
      const formData = new FormData();
      formData.append("name", voiceName);
      formData.append("voice_id", voiceId);

      const res = await fetch("/api/voices/from-recordings", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        navigate("/my-voices");
      } else {
        alert("Failed to save voice.");
      }
    } catch {
      alert("Error saving voice.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 pb-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Record Voice</h1>
          <p className="text-muted-foreground mt-1">
            Record sentences to build a high-quality custom voice
          </p>
        </div>
        {totalRecorded >= 5 && (
          <Button onClick={() => setShowSave(true)}>
            <Save className="h-4 w-4 mr-2" />
            Save Voice ({totalRecorded} recordings)
          </Button>
        )}
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">
            {totalRecorded} / {scripts.length} sentences
          </span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Sentence grid */}
      <div className="flex gap-1.5 flex-wrap">
        {scripts.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            className={`h-8 w-8 rounded text-xs font-medium transition-colors ${
              i === index
                ? "bg-primary text-primary-foreground"
                : i in recordings
                ? "bg-green-500 text-white"
                : "bg-secondary text-secondary-foreground hover:bg-accent"
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>

      {/* Current sentence */}
      {scripts[index] && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-8">
            <p className="text-center text-2xl leading-relaxed font-medium">
              {scripts[index].text}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recording controls */}
      <div className="flex flex-col items-center gap-4">
        {/* Playback if recorded */}
        {recordings[index] && recordings[index] !== "saved" && (
          <div className="flex items-center gap-3 w-full max-w-md">
            <audio controls src={recordings[index]} className="flex-1 h-10" />
            <Button variant="ghost" size="icon" onClick={deleteRecording}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        )}

        {/* Status text */}
        <p className="text-sm text-muted-foreground">
          {status === "ready" && !recordings[index] && "Press the mic button to start"}
          {status === "ready" && recordings[index] && "Recorded! Move to next sentence or re-record"}
          {status === "countdown" && `Starting in ${countdown}...`}
          {status === "recording" && "Recording — press stop when done"}
        </p>

        {/* Control buttons */}
        <div className="flex items-center gap-6">
          <Button
            variant="outline"
            size="icon"
            className="h-12 w-12 rounded-full"
            onClick={() => goTo(index - 1)}
            disabled={index === 0}
          >
            <ChevronLeft className="h-6 w-6" />
          </Button>

          {/* Main record button */}
          <button
            onClick={() => {
              if (status === "recording") stopRecording();
              else if (!recordings[index]) startCountdown();
            }}
            disabled={!!recordings[index] && status !== "recording"}
            className={`h-16 w-16 rounded-full flex items-center justify-center transition-all ${
              status === "recording"
                ? "bg-destructive hover:bg-destructive/90 scale-110"
                : recordings[index]
                ? "bg-green-500 cursor-default"
                : "bg-primary hover:bg-primary/90"
            }`}
          >
            {status === "countdown" ? (
              <span className="text-white text-2xl font-bold">{countdown}</span>
            ) : recordings[index] && status !== "recording" ? (
              <Check className="h-8 w-8 text-white" />
            ) : status === "recording" ? (
              <Square className="h-6 w-6 text-white fill-white" />
            ) : (
              <Mic className="h-8 w-8 text-white" />
            )}
          </button>

          <Button
            variant="outline"
            size="icon"
            className="h-12 w-12 rounded-full"
            onClick={() => goTo(index + 1)}
            disabled={index >= scripts.length - 1}
          >
            <ChevronRight className="h-6 w-6" />
          </Button>
        </div>
      </div>

      {/* Save voice dialog */}
      {showSave && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardContent className="p-6 space-y-4">
              <h2 className="text-xl font-bold">Save Voice Profile</h2>
              <p className="text-sm text-muted-foreground">
                You have {totalRecorded} recordings. Give your voice a name to save it.
              </p>
              <Input
                placeholder="Voice name (e.g. My Voice)"
                value={voiceName}
                onChange={(e) => setVoiceName(e.target.value)}
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowSave(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveVoice}
                  disabled={!voiceName.trim() || saving}
                >
                  {saving ? "Saving..." : "Save Voice"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
