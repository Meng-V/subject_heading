import { useState } from 'react'
import { Upload, BookOpen, Sparkles, CheckCircle, Languages } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Textarea } from './components/ui/textarea'
import { Label } from './components/ui/label'

const API_BASE_URL = 'http://localhost:8000/api'

function App() {
  const [step, setStep] = useState(1)
  const [images, setImages] = useState([])
  const [metadata, setMetadata] = useState(null)
  const [topics, setTopics] = useState([])
  const [candidates, setCandidates] = useState([])
  const [subjects65x, setSubjects65x] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Step 1: Upload and OCR images
  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files)
    setImages(files)
    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      files.forEach(file => formData.append('images', file))

      const response = await fetch(`${API_BASE_URL}/ingest-images`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (data.success) {
        setMetadata(data.metadata)
        setStep(2)
      }
    } catch (err) {
      setError('Failed to process images: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 2: Generate East Asian-focused topics
  const handleGenerateTopics = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/generate-topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metadata }),
      })

      const data = await response.json()
      if (data.success) {
        setTopics(data.topics)
        setStep(3)
      }
    } catch (err) {
      setError('Failed to generate topics: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 3: Match authorities (LCSH + FAST with East Asian boost)
  const handleMatchAuthorities = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/authority-match-typed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topics: topics.map(t => ({ topic: t.topic, type: t.type })),
          vocabularies: ['lcsh', 'fast']
        }),
      })

      const data = await response.json()
      if (data.success) {
        setCandidates(data.matches)
        setStep(4)
      }
    } catch (err) {
      setError('Failed to match authorities: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 4: Build MARC 65X fields
  const handleBuild65X = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/build-65x`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics_with_candidates: candidates }),
      })

      const data = await response.json()
      if (data.success) {
        setSubjects65x(data.subjects_65x)
        setStep(5)
      }
    } catch (err) {
      setError('Failed to build MARC fields: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Languages className="h-12 w-12 text-indigo-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              East Asian Subject Heading Assistant
            </h1>
          </div>
          <p className="text-lg text-muted-foreground">
            AI-powered MARC subject headings for China, Korea, Japan, and East Asian collections
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            {['Upload', 'Topics', 'Match', 'Build', 'Review'].map((label, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step > idx + 1 ? 'bg-green-500 text-white' :
                  step === idx + 1 ? 'bg-indigo-600 text-white' :
                  'bg-gray-200 text-gray-400'
                }`}>
                  {step > idx + 1 ? <CheckCircle className="h-6 w-6" /> : idx + 1}
                </div>
                <span className="text-sm font-medium">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Step 1: Upload Images */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Book Images
              </CardTitle>
              <CardDescription>
                Upload cover, back, table of contents, or any pages with book information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-indigo-400 transition-colors">
                <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <Label htmlFor="image-upload" className="cursor-pointer">
                  <span className="text-lg font-medium text-indigo-600 hover:text-indigo-700">
                    Choose images
                  </span>
                  <span className="text-gray-500"> or drag and drop</span>
                </Label>
                <Input
                  id="image-upload"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <p className="text-sm text-gray-500 mt-2">PNG, JPG, JPEG up to 10MB each</p>
              </div>
              {loading && <p className="text-center mt-4 text-indigo-600">Processing images...</p>}
            </CardContent>
          </Card>
        )}

        {/* Step 2: Generate Topics */}
        {step === 2 && metadata && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Book Metadata Extracted
              </CardTitle>
              <CardDescription>
                Review and generate East Asian-focused subject topics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Title</Label>
                <p className="text-lg font-semibold">{metadata.title || 'N/A'}</p>
              </div>
              <div>
                <Label>Author</Label>
                <p>{metadata.author || 'N/A'}</p>
              </div>
              {metadata.summary && (
                <div>
                  <Label>Summary</Label>
                  <p className="text-sm text-muted-foreground">{metadata.summary}</p>
                </div>
              )}
              <Button onClick={handleGenerateTopics} disabled={loading} className="w-full">
                <Sparkles className="h-4 w-4 mr-2" />
                {loading ? 'Generating Topics...' : 'Generate East Asian Subject Topics'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Topic Candidates */}
        {step === 3 && topics.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Generated Topics ({topics.length})
              </CardTitle>
              <CardDescription>
                AI-generated topics with East Asian collection focus
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3">
                {topics.map((topic, idx) => (
                  <div key={idx} className="p-4 bg-secondary rounded-lg">
                    <p className="font-medium">{topic.topic}</p>
                    <p className="text-sm text-muted-foreground capitalize">Type: {topic.type}</p>
                  </div>
                ))}
              </div>
              <Button onClick={handleMatchAuthorities} disabled={loading} className="w-full">
                {loading ? 'Matching Authorities...' : 'Find Authority Headings (LCSH + FAST)'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Authority Candidates */}
        {step === 4 && candidates.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Authority Candidates</CardTitle>
              <CardDescription>
                Matched headings from LCSH and FAST vocabularies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {candidates.map((match, idx) => (
                <div key={idx} className="border rounded-lg p-4">
                  <p className="font-semibold text-indigo-600 mb-2">{match.topic}</p>
                  <div className="space-y-2">
                    {match.authority_candidates.slice(0, 3).map((cand, cidx) => (
                      <div key={cidx} className="flex justify-between items-center p-2 bg-secondary rounded">
                        <span className="text-sm">{cand.label}</span>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                          {cand.vocabulary.toUpperCase()} - {(cand.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <Button onClick={handleBuild65X} disabled={loading} className="w-full">
                {loading ? 'Building MARC Fields...' : 'Build MARC 65X Fields'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Final MARC 65X */}
        {step === 5 && subjects65x.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                MARC Subject Headings Ready
              </CardTitle>
              <CardDescription>
                {subjects65x.length} subject headings generated for East Asian collection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {subjects65x.map((subject, idx) => (
                <div key={idx} className="border rounded-lg p-4 bg-green-50">
                  <div className="flex justify-between items-start mb-2">
                    <code className="text-sm font-mono bg-white px-2 py-1 rounded">
                      {subject.tag} {subject.ind1 || '_'}{subject.ind2}
                    </code>
                    <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                      {subject.vocabulary.toUpperCase()}
                    </span>
                  </div>
                  {/* Display MARC subfields */}
                  <div className="font-mono text-sm bg-white p-2 rounded mb-2 overflow-x-auto">
                    {subject.subfields?.map((sf, sidx) => (
                      <span key={sidx} className="mr-1">
                        <span className="text-indigo-600 font-bold">${sf.code}</span>
                        <span className="ml-1">{sf.value}</span>
                      </span>
                    )) || <span>{subject.heading_string}</span>}
                  </div>
                  {subject.explanation && (
                    <p className="text-sm text-muted-foreground italic">{subject.explanation}</p>
                  )}
                  {subject.uri && (
                    <p className="text-xs text-muted-foreground mt-2">URI: {subject.uri}</p>
                  )}
                </div>
              ))}
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                  Process Another Book
                </Button>
                <Button onClick={() => navigator.clipboard.writeText(JSON.stringify(subjects65x, null, 2))} className="flex-1">
                  Copy MARC Data
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default App
