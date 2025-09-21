import React, { useMemo, useState, useEffect } from "react";
import { 
  Play, Pause, SkipBack, SkipForward, Maximize2, Search, Image as ImageIcon,
  User, CheckCircle2, Mic2, AlertTriangle, Gauge, Hash, Copy,
  ChevronRight, ChevronLeft, Smartphone, ShieldCheck, Eye, EyeOff,
} from "lucide-react";



/**
 * Forensic Tool – React single-file demo UI
 * ---------------------------------------------------------
 * - TailwindCSS styling (no imports needed in this canvas)
 * - Lucide icons
 * - All data is mocked locally; wire up real APIs as needed
 */



// ---------- Small UI Primitives ---------- Cars Colour
const Card = ({ className = "", children }) => (
  <div className={`rounded-2xl bg-black-200 border border-zinc-800 shadow-xl ${className}`}>{children}</div>
);
//bg-zinc-900/60 Actual card colour
const SectionTitle = ({ children, right }) => (
  <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800/80">
    <h3 className="text-white font-medium tracking-wide uppercase text-xs">{children}</h3>
    {right}
  </div>
);

const Badge = ({ tone = "slate", children }) => {
  const tones = {
    amber: "bg-amber-600/15 text-amber-300 ring-1 ring-amber-500/30",
    green: "bg-emerald-600/15 text-emerald-300 ring-1 ring-emerald-500/30",
    slate: "bg-zinc-600/20 text-zinc-300 ring-1 ring-zinc-500/30",
    blue: "bg-sky-600/15 text-sky-300 ring-1 ring-sky-500/30",
  };
  return (
    <span className={`px-2.5 py-0.5 text-[10px] rounded-full font-medium ${tones[tone]}`}>{children}</span>
  );
};

const IconButton = ({ icon: Icon, label, onClick, active=false }) => (
  <button
    onClick={onClick}
    className={`h-9 w-9 inline-flex items-center justify-center rounded-xl border transition ${active ? "bg-zinc-800/80 border-zinc-700" : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700"}`}
    title={label}
  >
    <Icon className="h-4.5 w-4.5 text-zinc-300" />
  </button>
);

const ProgressBar = ({ label, value }) => (
  <div className="flex items-center gap-3">
    <div className="w-24 text-xs text-zinc-400">{label}</div>
    <div className="flex-1 h-2 rounded-full bg-zinc-800 overflow-hidden">
      <div className="h-full bg-sky-500/80" style={{ width: `${value}%` }} />
    </div>
    <div className="w-10 text-right text-xs text-zinc-400">{value}%</div>
  </div>
);

// ---------- Visualization Components ----------
const DonutGauge = ({ value = 87 }) => {
  const size = 160;
  const stroke = 14;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (value / 100) * c;
  return (
    <div className="relative w-[160px] h-[160px]">
      <svg viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
        <circle cx={size/2} cy={size/2} r={r} strokeWidth={stroke} className="fill-none stroke-zinc-800" />
        <circle cx={size/2} cy={size/2} r={r} strokeWidth={stroke} className="fill-none stroke-sky-500" strokeDasharray={`${dash} ${c-dash}`} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center">
          <div className="text-4xl font-semibold text-zinc-100">{value}%</div>
          <div className="text-[11px] text-zinc-400 tracking-wide">CALIBRATED</div>
        </div>
      </div>
    </div>
  );
};

const Sparkline = ({ data = [], height = 64, stroke = 2, className = "" }) => {
  const width = 540;
  const points = useMemo(() => {
    if (!data.length) return "";
    const max = Math.max(...data);
    const min = Math.min(...data);
    const scaleX = (i) => (i / (data.length - 1)) * width;
    const scaleY = (v) => height - ((v - min) / (max - min || 1)) * height;
    return data.map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ");
  }, [data]);

  return (
    <svg className={`w-full ${className}`} width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline fill="none" stroke="#0f0e0eff" strokeWidth={stroke} points={`0,${height-1} ${width},${height-1}`} />
      <polyline fill="none" stroke="#b5f25aff" strokeWidth={stroke} points={points} />
    </svg>
  );
};

// ---------- Mock Video Area ----------
const VideoPlayerMock = ({ playing }) => {
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-800 to-zinc-900">
      {/* Face silhouette */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-[340px] h-[340px] rounded-full bg-zinc-700/20 blur-0" />
      </div>
      {/* Eyes highlight boxes */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-[140px] flex gap-16">
        {[0,1].map((i) => (
          <div key={i} className="w-14 h-10 rounded-md border-2 border-amber-400 shadow-[0_0_0_2px_rgba(250,204,21,0.25)]" />
        ))}
      </div>
      {/* Play pulse */}
      {playing && (
        <div className="absolute bottom-4 right-4 text-[11px] text-zinc-400 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> LIVE
        </div>
      )}
    </div>
  );
};

// ---------- Main App ----------
export default function ForensicToolDashboard() {
  const [user, setUser] = useState(() => localStorage.getItem("username") || null);
  const [authenticated, setAuthenticated] = useState(!!user);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(42);
  const [score, setScore] = useState(0);

  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [meta, setMeta] = useState(null);
  const [maskImage, setMaskImage] = useState(null);
  const [maskOpacity, setMaskOpacity] = useState(0.5); // default 50%



  const handleAnalyze = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      // ✅ Store the entire backend result
      setResult(data);

      // Optional: set mask or processed image if they exist
      if (data.mask) setMaskImage(`data:image/png;base64,${data.mask}`);
      if (data.image) setProcessedImage(`data:image/png;base64,${data.image}`);

      // Remove the separate score state entirely
      // setScore(data.confidence * 100);  <--- remove this
    } catch (err) {
      console.error("Error analyzing image:", err);
    }
  };

  const handleLogin = async () => {
    setLoginError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("username", data.username);
        setUser(data.username);
        setAuthenticated(true);
      } else {
        const errorData = await response.json();
        setLoginError(errorData.detail || "Login failed");
      }
    } catch (err) {
      setLoginError("Network error: " + err.message);
    }
  };



  const handleMetadata = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://localhost:5000/metadata", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      setMeta(data);

    } catch (err) {
      console.error("Error fetching metadata:", err);
    }
  };




  const getAuthHeaders = () => {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  };
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setProgress(p => (p >= 100 ? 0 : p + 1)), 120);
    return () => clearInterval(id);
  }, [playing]);

  const confidence = useMemo(() => Array.from({length: 90}, (_,i) => 50 + Math.sin(i/5)*18 + (Math.random()*8-4)), []);
  const confluence = useMemo(() => Array.from({length: 70}, (_,i) => 40 + Math.cos(i/6)*14 + (Math.random()*6-3)), []);
  const [processedImage, setProcessedImage] = useState(null);


  const copy = async (txt) => {
    try { await navigator.clipboard.writeText(txt); alert("Copied to clipboard"); } catch {}
  };

  const confidencePercent = result?.confidence != null ? result.confidence * 100 : 0;

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-900">
        <div className="bg-zinc-950 p-8 rounded-2xl shadow-lg w-[320px]">
          <h2 className="text-white text-xl font-semibold mb-6 text-center">Login</h2>
          <input
            type="text"
            placeholder="Username"
            value={loginUsername}
            onChange={(e) => setLoginUsername(e.target.value)}
            className="w-full mb-4 px-4 py-2 rounded-lg bg-zinc-800 text-white border border-zinc-700"
          />
          <input
            type="password"
            placeholder="Password"
            value={loginPassword}
            onChange={(e) => setLoginPassword(e.target.value)}
            className="w-full mb-4 px-4 py-2 rounded-lg bg-zinc-800 text-white border border-zinc-700"
          />
          {loginError && <div className="text-red-500 text-sm mb-2">{loginError}</div>}
          <button
            onClick={handleLogin}
            className="w-full py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold"
          >
            Login
          </button>
        </div>
      </div>
    );
  }


  return (
    <div className="min-h-screen w-full bg-black text-zinc-100">
      <div className="max-w-[1600px] mx-auto grid grid-cols-[260px_1fr_380px] gap-6 p-6">
        
        {/* Left column = new box + sidebar */}
        <div className="flex flex-col gap-6 sticky top-6 self-start h-fit">
          {/* New Top-Left Box */}
          <Card className="h-[500px] flex flex-col px-5 pt-4 pb-3">
            <div className="text-lg font-semibold tracking-tight">Upload an Image</div>
            <div className="mt-3 text-sm text-zinc-400">
              Choose an image to analyze.
            </div>

            {/* File input */}
            <div className="mt-4">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setSelectedFile(file);                 // store file for later use
                  setPreview(URL.createObjectURL(file)); // generate preview URL
                }}
                className="block w-full text-sm text-zinc-400
                          file:mr-4 file:py-2 file:px-4
                          file:rounded-lg file:border-0
                          file:text-sm file:font-semibold
                          file:bg-sky-600 file:text-white
                          hover:file:bg-sky-500"
              />
            </div>
            {preview && (
              <div className="mt-4 flex-1 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950 flex items-center justify-center">
                <img src={preview} alt="Preview" className="max-h-full object-contain" />
              </div>
            )}
            {/* Fake result
            {result && (
              <pre className="mt-3 text-xs bg-zinc-900 p-2 rounded overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            )} */}
            {/* Upload button */}
            <button
              onClick={handleAnalyze}
              disabled={!selectedFile}
              className="mt-3 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm"
            >
              Analyze Image
            </button>



            
            
          </Card>
          

          {/* Sidebar */}
          <div className="sticky top-[100px] h-[calc(100vh-100px)]">
            <Card className="h-full flex flex-col">
              <div className="px-5 pt-4 pb-3">
                <div className="text-lg font-semibold tracking-tight">Cases</div>
                <div className="mt-3 relative">
                  <input
                    placeholder="Search"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-sky-600"
                  />
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
                </div>
              </div>

              <div className="px-3 space-y-1.5 overflow-y-auto">
                <SidebarItem icon={ImageIcon} label="Image" badge={<Badge tone="amber">SUSPECT</Badge>} active />
                <SidebarItem icon={User} label="Suspect" badge={<Badge tone="slate">SUSPECT</Badge>} />
                <SidebarItem icon={CheckCircle2} label="Verified" badge={<Badge tone="green">VERIFIED</Badge>} />
                <SidebarItem icon={Mic2} label="Audio" badge={<Badge tone="green">VERIFIED</Badge>} />
              </div>

              <div className="mt-auto px-5 py-4 border-t border-zinc-800/80">
                <div className="text-sm text-zinc-400 mb-2">Ingest</div>
                <ProgressBar label="Engines" value={90} />
                <div className="h-2" />
                <ProgressBar label="Frames" value={72} />
                <div className="h-2" />
                <ProgressBar label="Features" value={54} />
                <div className="h-2" />
                <ProgressBar label="Classify" value={31} />
              </div>
            </Card>
          </div>
        </div>

        {/* Main content */}
        <main className="space-y-6">
          {/* Header strip */}
          <Card>
            <div className="grid grid-cols-3 items-center px-5 py-3">
              <div className="text-sm text-zinc-400">
                <div className="uppercase tracking-widest text-[10px] text-zinc-500">Case ID</div>
                <div className="font-medium text-zinc-200">source.mp4</div>
              </div>
              <div className="text-sm text-zinc-400">
                <div className="uppercase tracking-widest text-[10px] text-zinc-500">Analyst</div>
                <div className="font-medium text-zinc-200">Analyst</div>
              </div>
              <div className="text-sm text-right text-zinc-400">
                <div className="uppercase tracking-widest text-[10px] text-zinc-500">Model</div>
                <div className="font-medium text-zinc-200">v1.5.0</div>
              </div>
            </div>
          </Card>

          {/* Viewer & Transport */}
          <Card className="p-4">
            <div className="flex items-center justify-between px-1 pb-3">
              <div className="flex items-center gap-2">
                <IconButton icon={SkipBack} label="Back" />
                {playing ? (
                  <IconButton icon={Pause} label="Pause" onClick={() => setPlaying(false)} active />
                ) : (
                  <IconButton icon={Play} label="Play" onClick={() => setPlaying(true)} />
                )}
                <IconButton icon={SkipForward} label="Forward" />
              </div>
              <div className="flex items-center gap-2">
                <div className="text-xs text-zinc-400">{Math.floor(progress)}%</div>
                <div className="w-[360px] h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-sky-500" style={{width:`${progress}%`}} />
                </div>
                <IconButton icon={Maximize2} label="Fullscreen" />
              </div>
            </div>

            {preview ? (
              <div className="relative w-full h-[500px] rounded-lg border border-zinc-800 overflow-hidden">
                {/* Original image */}
                <img
                  src={preview}
                  alt="Original"
                  className="absolute top-1/2 left-1/2 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain"
                />

                {/* Mask overlay */}
                {maskImage && (
                  <img
                    src={maskImage}
                    alt="Forgery Mask"
                    className="absolute top-1/2 left-1/2 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain pointer-events-none"
                    style={{ opacity: maskOpacity }}
                  />
                )}

                {/* Optional opacity slider */}
                {maskImage && (
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={maskOpacity}
                    onChange={(e) => setMaskOpacity(parseFloat(e.target.value))}
                    className="absolute bottom-2 left-1/2 -translate-x-1/2 w-3/4"
                  />
                )}
              </div>
            ) : (
              <VideoPlayerMock playing={playing} />
            )}



            
            {/* Forgery Confidence Bar */}
            <Card className="mt-4">
              <SectionTitle
                right={<Badge tone={confidencePercent >= 50 ? "red" : "green"}>
                  {confidencePercent >= 50 ? "FAKE" : "REAL"}
                </Badge>}
                className="border-b-0"
              >
                Forgery Confidence
              </SectionTitle>
              <div className="px-3 pb-3 pt-2">
                <div className="relative h-6 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${confidencePercent >= 50 ? "bg-red-600" : "bg-emerald-500"}`}
                    style={{ width: `${confidencePercent}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-zinc-100">
                    {confidencePercent >= 50 ? `Fake ${confidencePercent.toFixed(1)}%` : `Real ${confidencePercent.toFixed(1)}%`}
                  </div>
                </div>
              </div>
            </Card>
          </Card>

          {/* Bottom ingest (compact) */}
          <Card className="px-5 py-4">
            <div className="text-sm text-zinc-400 mb-2">Ingest</div>
            <div className="grid grid-cols-4 gap-4">
              <MiniProgress label="Engines" value={90} />
              <MiniProgress label="Frames" value={72} />
              <MiniProgress label="Features" value={54} />
              <MiniProgress label="Classify" value={31} />
            </div>
          </Card>
        </main>

        {/* Right rail */}
        <aside className="space-y-6">
          
          <Card>
            <SectionTitle className="text-white">User</SectionTitle>
            <div className="p-5 text-center text-zinc-500 text-lg font-semibold space-y-4">
              {user ? (
                <>
                  <div>Logged in as: {user}</div>
                  <button
                    className="px-6 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold"
                    onClick={() => {
                      // Clear token and user info
                      localStorage.removeItem("access_token");
                      localStorage.removeItem("username");
                      setUser(null);
                      // Redirect to login page
                      window.location.href = "/login"; 
                    }}
                  >
                    Logout
                  </button>
                </>
              ) : (
                <div>Not logged in</div>
              )}
            </div>
          </Card>


         
     
          <Card>
            <SectionTitle right={
              <button
                onClick={handleMetadata}
                className="text-xs text-sky-400 hover:underline"
              >
                Analyze
              </button>
            }>
              Metadata & Provenance
            </SectionTitle>
            <div className="p-5 text-xs text-zinc-300 space-y-4">
              {meta ? (
                <>
                  <pre>
          <div className="p-5 text-xs text-zinc-300 space-y-1">
            <div className="mt-2 font-semibold text-sky-500">[File Information]</div>
            <div>File: {selectedFile?.name}</div>
            <div>Size: {meta.size_bytes.toLocaleString()} bytes</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-300">SHA-256:</span>
              <code
                className="text-zinc-300 truncate max-w-[200px]"
                title={meta.sha256} // shows full SHA on hover
              >
                {meta.sha256}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(meta.sha256)}
                className="ml-auto inline-flex items-center gap-1 text-xs text-sky-400 hover:underline"
              >
                <Copy className="h-3.5 w-3.5"/>Copy
              </button>
            </div>

            <div className="mt-2 font-semibold text-sky-500">[File Timestamps]</div>
            <div>Created: {meta.created}</div>
            <div>Modified: {meta.modified}</div>
            <div>Analysed: {meta.analysed}</div>

            <div className="mt-2 font-semibold text-sky-500">[Camera Information]</div>
            <div>Make: {meta.make || "N/A"}</div>
            <div>Model: {meta.model || "N/A"}</div>
            <div>Serial Number: {meta.serial || "N/A"}</div>
            <div>Lens Model: {meta.lens || "N/A"}</div>
            <div>Date Taken: {meta.date_taken || "N/A"}</div>

            <div className="mt-2 font-semibold text-sky-500">[Location Data]</div>
            <div>Latitude: {meta.latitude != null ? meta.latitude.toFixed(6) : "N/A"}</div>
            <div>Longitude: {meta.longitude != null ? meta.longitude.toFixed(6) : "N/A"}</div>
            <div>Altitude: {meta.altitude != null ? meta.altitude.toFixed(2) + " m" : "N/A"}</div>

            <div className="mt-2 font-semibold text-sky-500">[Software / Editing]</div>
            <div className="flex flex-col gap-1 text-xs">
              {meta.software && (
                <div className="flex items-center gap-2">
                  <span className="text-zinc-300">Software:</span>
                  <code
                    className="text-zinc-300 truncate max-w-[200px]"
                    title={meta.software}
                  >
                    {meta.software}
                  </code>
                </div>
              )}
              {meta.description && (
                <div className="flex items-center gap-2">
                  <span className="text-zinc-300">Description:</span>
                  <code
                    className="text-zinc-300 truncate max-w-[200px]"
                    title={meta.description}
                  >
                    {meta.description}
                  </code>
                </div>
              )}
            </div>
          </div>

                  </pre>
                </>
              ) : (
                <div className="text-zinc-400">
                  Upload an image and click **Analyze** to view metadata.
                </div>
              )}
            </div>
          </Card>


           

          <Card>
            <SectionTitle>Mobile Check</SectionTitle>
            <div className="p-5">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex items-center gap-3 text-sm text-zinc-300"><Smartphone className="h-4 w-4"/> BagOAT</div>
                <div className="mt-4 grid grid-cols-[1fr_auto] items-center gap-4">
                  <div>
                    <div className="text-xs text-zinc-500">Pulldown</div>
                    <div className="text-2xl font-semibold">{score}%</div>
                  </div>
                  <button className="px-3 py-1.5 rounded-lg bg-sky-600/90 hover:bg-sky-500 text-sm">Report</button>
                </div>
              </div>
            </div>
          </Card>




          <Card>
            <SectionTitle right={<div className="text-sky-400 text-xs flex items-center gap-1">SCORE <ChevronRight className="h-3 w-3"/></div>}>Findings</SectionTitle>
            <div className="p-5">
              <div className="flex items-center gap-6">
                <DonutGauge value={score} />
                <div className="space-y-4">
                  <Row icon={AlertTriangle} iconClass="text-amber-300" title="FFT anomaly in T‑zone" />
                  <Row icon={Eye} iconClass="text-amber-300" title="Eye blink inconsistencies" />
                  <Row icon={AlertTriangle} iconClass="text-amber-300" title="Incoherent head pose" />
                </div>
              </div>
            </div>
          </Card>
          
      







        </aside>
      </div>
    </div>
  );
}

const SidebarItem = ({ icon: Icon, label, badge, active=false }) => (
  <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition border ${active?"bg-zinc-900/70 border-zinc-700":"bg-zinc-950 border-zinc-900 hover:border-zinc-800"}`}>
    <Icon className="h-4.5 w-4.5 text-zinc-300"/>
    <span className="text-sm flex-1 text-zinc-200 text-left">{label}</span>
    {badge}
  </button>
);

const Row = ({ icon: Icon, title, iconClass }) => (
  <div className="flex items-center gap-2 text-sm">
    <Icon className={`h-4.5 w-4.5 ${iconClass}`} />
    <span className="text-zinc-300">{title}</span>
  </div>
);

const MiniProgress = ({ label, value }) => (
  <div>
    <div className="text-[11px] text-zinc-500 mb-1">{label}</div>
    <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
      <div className="h-full bg-sky-500" style={{ width: `${value}%` }} />
    </div>
  </div>
);
