import { useState } from 'react'
import { Upload, BookOpen, Sparkles, CheckCircle, Languages, Plus, Trash2, Edit3, FileText, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Textarea } from './components/ui/textarea'
import { Label } from './components/ui/label'

const API_BASE_URL = 'http://localhost:8000/api'

// Empty metadata template with all fields
const emptyMetadata = {
  title: '',
  author: '',
  publisher: '',
  pub_place: '',
  pub_year: '',
  language: '',
  isbn: '',
  edition: '',
  series: '',
  summary: '',
  subjects_hint: '',
  table_of_contents: [],
  preface_snippets: [],
  notes: ''
}

function App() {
  const [step, setStep] = useState(1)
  const [images, setImages] = useState([])
  const [metadata, setMetadata] = useState(null)
  const [topics, setTopics] = useState([])
  const [candidates, setCandidates] = useState([])
  const [subjects65x, setSubjects65x] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [manualEntry, setManualEntry] = useState(false)

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

  // Start manual entry mode
  const handleManualEntry = () => {
    setManualEntry(true)
    setMetadata({ ...emptyMetadata })
    setStep(2)
  }

  // Update metadata field
  const updateMetadata = (field, value) => {
    setMetadata(prev => ({ ...prev, [field]: value }))
  }

  // Update topic
  const updateTopic = (idx, field, value) => {
    setTopics(prev => prev.map((t, i) => i === idx ? { ...t, [field]: value } : t))
  }

  // Add new topic
  const addTopic = () => {
    setTopics(prev => [...prev, { topic: '', type: 'topical' }])
  }

  // Remove topic
  const removeTopic = (idx) => {
    setTopics(prev => prev.filter((_, i) => i !== idx))
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

        {/* Step 1: Upload Images OR Manual Entry */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Book Images or Enter Manually
              </CardTitle>
              <CardDescription>
                Upload cover, back, table of contents, or any pages with book information. Or enter metadata manually.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Image Upload Option */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors">
                <Upload className="h-10 w-10 mx-auto mb-3 text-gray-400" />
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
              {loading && <p className="text-center text-indigo-600">Processing images with AI...</p>}
              
              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-muted-foreground">Or</span>
                </div>
              </div>
              
              {/* Manual Entry Option */}
              <Button variant="outline" onClick={handleManualEntry} className="w-full" disabled={loading}>
                <FileText className="h-4 w-4 mr-2" />
                Enter Metadata Manually
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Editable Metadata Form */}
        {step === 2 && metadata && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Edit3 className="h-5 w-5" />
                {manualEntry ? 'Enter Book Metadata' : 'Review & Edit Extracted Metadata'}
              </CardTitle>
              <CardDescription>
                {manualEntry ? 'Fill in the book information below' : 'Review the extracted information and make any corrections before generating topics'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    value={metadata.title || ''}
                    onChange={(e) => updateMetadata('title', e.target.value)}
                    placeholder="Enter book title"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="author">Author(s)</Label>
                  <Input
                    id="author"
                    value={metadata.author || ''}
                    onChange={(e) => updateMetadata('author', e.target.value)}
                    placeholder="Author name(s)"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="publisher">Publisher</Label>
                  <Input
                    id="publisher"
                    value={metadata.publisher || ''}
                    onChange={(e) => updateMetadata('publisher', e.target.value)}
                    placeholder="Publisher name"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="pub_place">Publication Place</Label>
                  <Input
                    id="pub_place"
                    value={metadata.pub_place || ''}
                    onChange={(e) => updateMetadata('pub_place', e.target.value)}
                    placeholder="City, Country"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="pub_year">Publication Year</Label>
                  <Input
                    id="pub_year"
                    value={metadata.pub_year || ''}
                    onChange={(e) => updateMetadata('pub_year', e.target.value)}
                    placeholder="YYYY"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="language">Language</Label>
                  <Input
                    id="language"
                    value={metadata.language || ''}
                    onChange={(e) => updateMetadata('language', e.target.value)}
                    placeholder="e.g., Chinese, Japanese, Korean"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="isbn">ISBN</Label>
                  <Input
                    id="isbn"
                    value={metadata.isbn || ''}
                    onChange={(e) => updateMetadata('isbn', e.target.value)}
                    placeholder="ISBN-10 or ISBN-13"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="edition">Edition</Label>
                  <Input
                    id="edition"
                    value={metadata.edition || ''}
                    onChange={(e) => updateMetadata('edition', e.target.value)}
                    placeholder="e.g., 2nd edition, revised"
                    className="mt-1"
                  />
                </div>
                <div className="col-span-2">
                  <Label htmlFor="series">Series</Label>
                  <Input
                    id="series"
                    value={metadata.series || ''}
                    onChange={(e) => updateMetadata('series', e.target.value)}
                    placeholder="Series title if part of a series"
                    className="mt-1"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="subjects_hint">Subject Hints (from OCR or your knowledge)</Label>
                <Textarea
                  id="subjects_hint"
                  value={metadata.subjects_hint || ''}
                  onChange={(e) => updateMetadata('subjects_hint', e.target.value)}
                  placeholder="Keywords, themes, or subject terms that describe this book's content"
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="summary">Summary / Description</Label>
                <Textarea
                  id="summary"
                  value={metadata.summary || ''}
                  onChange={(e) => updateMetadata('summary', e.target.value)}
                  placeholder="Book summary, back cover text, or description"
                  className="mt-1 min-h-[100px]"
                />
              </div>
              <div>
                <Label htmlFor="toc">Table of Contents (one item per line)</Label>
                <Textarea
                  id="toc"
                  value={Array.isArray(metadata.table_of_contents) ? metadata.table_of_contents.join('\n') : (metadata.table_of_contents || '')}
                  onChange={(e) => updateMetadata('table_of_contents', e.target.value.split('\n').filter(l => l.trim()))}
                  placeholder="Chapter 1: Introduction\nChapter 2: History..."
                  className="mt-1 min-h-[80px]"
                />
              </div>
              {/* Show info message if OCR had issues */}
              {metadata.notes && metadata.notes.includes('could not be extracted') && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-amber-800">
                    <strong>OCR Notice:</strong> {metadata.notes}
                  </div>
                </div>
              )}
              <div>
                <Label htmlFor="notes">Additional Notes</Label>
                <Textarea
                  id="notes"
                  value={metadata.notes && !metadata.notes.includes('could not be extracted') ? metadata.notes : ''}
                  onChange={(e) => updateMetadata('notes', e.target.value)}
                  placeholder="Any additional information that might help with subject heading generation"
                  className="mt-1"
                />
              </div>
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => { setStep(1); setManualEntry(false); }} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleGenerateTopics} 
                  disabled={loading || !metadata.title || metadata.title === 'Please enter title'} 
                  className="flex-1"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {loading ? 'Generating Topics...' : 'Generate East Asian Subject Topics'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Editable Topic Candidates */}
        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Edit Topics ({topics.length})
              </CardTitle>
              <CardDescription>
                Review, edit, add, or remove topics before matching to authority headings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {topics.map((topic, idx) => (
                  <div key={idx} className="flex gap-2 items-start p-3 bg-secondary rounded-lg">
                    <div className="flex-1 space-y-2">
                      <Input
                        value={topic.topic}
                        onChange={(e) => updateTopic(idx, 'topic', e.target.value)}
                        placeholder="Topic text"
                        className="bg-white"
                      />
                      <select
                        value={topic.type}
                        onChange={(e) => updateTopic(idx, 'type', e.target.value)}
                        className="w-full px-3 py-2 text-sm border rounded-md bg-white"
                      >
                        <option value="topical">Topical (subject matter)</option>
                        <option value="geographic">Geographic (place)</option>
                        <option value="genre">Genre/Form (document type)</option>
                      </select>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTopic(idx)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
              <Button variant="outline" onClick={addTopic} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Topic
              </Button>
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleMatchAuthorities} 
                  disabled={loading || topics.filter(t => t.topic.trim()).length === 0} 
                  className="flex-1"
                >
                  {loading ? 'Matching Authorities...' : 'Find Authority Headings (LCSH + FAST)'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Authority Candidates - Editable */}
        {step === 4 && candidates.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Authority Candidates</CardTitle>
              <CardDescription>
                Review and remove unwanted headings. Click the trash icon to remove topics or individual candidates.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {candidates.map((match, idx) => (
                <div key={idx} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <p className="font-semibold text-indigo-600">{match.topic}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setCandidates(prev => prev.filter((_, i) => i !== idx))}
                      className="text-destructive hover:text-destructive -mt-1 -mr-2"
                      title="Remove this topic"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {match.authority_candidates.map((cand, cidx) => (
                      <div key={cidx} className="flex justify-between items-center p-2 bg-secondary rounded group">
                        <span className="text-sm flex-1">{cand.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                            {cand.vocabulary.toUpperCase()} - {(cand.score * 100).toFixed(0)}%
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setCandidates(prev => prev.map((m, i) => 
                                i === idx 
                                  ? { ...m, authority_candidates: m.authority_candidates.filter((_, ci) => ci !== cidx) }
                                  : m
                              ))
                            }}
                            className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                            title="Remove this candidate"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    {match.authority_candidates.length === 0 && (
                      <p className="text-sm text-muted-foreground italic p-2">No candidates remaining - this topic will be skipped</p>
                    )}
                  </div>
                </div>
              ))}
              {candidates.filter(c => c.authority_candidates.length > 0).length === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  No candidates selected. Go back to add more topics.
                </div>
              )}
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(3)} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleBuild65X} 
                  disabled={loading || candidates.filter(c => c.authority_candidates.length > 0).length === 0} 
                  className="flex-1"
                >
                  {loading ? 'Building MARC Fields...' : 'Build MARC 65X Fields'}
                </Button>
              </div>
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
                    <p className="text-xs text-muted-foreground mt-2">URI: <a href={subject.uri} target="_blank">{subject.uri}</a></p>
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
