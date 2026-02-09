'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Bot, Activity, Brain, Heart, TrendingUp, Zap, Eye, X, Send, User, Maximize2, RotateCcw, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'

// Dynamic import for Three.js + OpenUSD viewer (no SSR - requires WebGL)
const DigitalTwinViewer = dynamic(
  () => import('@/components/digital-twin/DigitalTwinViewer'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[600px] bg-gradient-to-br from-slate-900 to-blue-900 rounded-lg flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4" />
          <p className="text-lg">Loading 3D Digital Twin...</p>
          <p className="text-sm text-gray-400 mt-2">Initializing Three.js + OpenUSD renderer</p>
        </div>
      </div>
    ),
  }
)

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function DigitalTwinPage() {
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [showFullModel, setShowFullModel] = useState(false)
  const [use3DViewer, setUse3DViewer] = useState(true)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI health assistant powered by your Digital Twin data. I can help you understand your health metrics, provide insights based on your trends, and answer questions about your wellness journey. How can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [modelRotation, setModelRotation] = useState(0)

  const healthSystems = [
    { id: 'immune', name: 'Immune System', status: 85, icon: Zap, color: 'text-blue-500', description: 'CD4 count stable, viral load undetectable. Immune response showing positive trends.' },
    { id: 'cardiovascular', name: 'Cardiovascular', status: 92, icon: Heart, color: 'text-red-500', description: 'Heart rate variability optimal. Blood pressure within healthy range.' },
    { id: 'nervous', name: 'Nervous System', status: 78, icon: Brain, color: 'text-purple-500', description: 'Cognitive function stable. Sleep quality could be improved for better neural recovery.' },
    { id: 'metabolic', name: 'Metabolic', status: 88, icon: Activity, color: 'text-green-500', description: 'Metabolism functioning well. Glucose levels stable. Consider increased physical activity.' },
  ]

  // AI Chat responses based on context
  const getAIResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase()

    if (lowerMessage.includes('cd4') || lowerMessage.includes('immune')) {
      return "Based on your Digital Twin analysis, your immune system is performing well at 85%. Your CD4 count has been stable over the past 30 days, and the simulation predicts continued stability with your current medication adherence rate of 95%."
    }
    if (lowerMessage.includes('heart') || lowerMessage.includes('cardio')) {
      return "Your cardiovascular health score is excellent at 92%. Your Digital Twin shows optimal heart rate variability and healthy blood pressure trends. The model suggests maintaining your current activity level of approximately 8,400 daily steps."
    }
    if (lowerMessage.includes('sleep') || lowerMessage.includes('tired') || lowerMessage.includes('energy')) {
      return "Your Digital Twin has identified sleep quality as an area for improvement. The nervous system score of 78% reflects irregular sleep patterns. The simulation suggests establishing a consistent sleep schedule could improve your overall wellness score by 5-8%."
    }
    if (lowerMessage.includes('medication') || lowerMessage.includes('adherence')) {
      return "Your medication adherence rate is excellent at 95% over the past 30 days. Your Digital Twin predicts that maintaining this level will keep your health metrics stable. The model shows a 95% confidence in positive health outcomes at this adherence rate."
    }
    if (lowerMessage.includes('weight') || lowerMessage.includes('diet') || lowerMessage.includes('nutrition')) {
      return "Based on metabolic modeling, your Digital Twin suggests you're on track to reach your target weight in approximately 6 weeks at your current pace. The simulation recommends increasing vitamin D intake for optimal immune support."
    }
    if (lowerMessage.includes('stress') || lowerMessage.includes('anxiety') || lowerMessage.includes('mental')) {
      return "Your Digital Twin's neural pathway analysis suggests stress levels are within normal range. However, incorporating 10-15 minutes of daily mindfulness practice could improve both your nervous system score and overall wellness index by 3-5%."
    }

    return "I've analyzed your Digital Twin data for relevant insights. Your overall health index is 86%, indicating excellent health trends. Is there a specific body system or health metric you'd like me to focus on? I can provide detailed analysis of your immune, cardiovascular, nervous, or metabolic systems."
  }

  const handleSendChat = async () => {
    if (!chatInput.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput,
      timestamp: new Date(),
    }

    setChatMessages((prev) => [...prev, userMessage])
    const userInput = chatInput
    setChatInput('')
    setChatLoading(true)

    // Simulate AI processing time
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 500))

    const aiMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: getAIResponse(userInput),
      timestamp: new Date(),
    }
    setChatMessages((prev) => [...prev, aiMessage])
    setChatLoading(false)
  }

  const handleChatKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendChat()
    }
  }

  const rotateModel = () => {
    setModelRotation((prev) => (prev + 45) % 360)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold gradient-text flex items-center">
          <Bot className="h-8 w-8 mr-3" />
          Digital Twin Visualization
        </h1>
        <p className="text-gray-600 mt-2">
          Real-time simulation of your health data and predicted outcomes
        </p>
      </div>

      {/* Overall Health Score */}
      <Card className="apple-card bg-gradient-to-br from-blue-50 to-purple-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex-1 text-center md:text-left">
              <h3 className="text-lg font-medium text-gray-600 mb-2">Overall Health Index</h3>
              <div className="text-5xl font-bold gradient-text mb-2">86%</div>
              <p className="text-sm text-gray-600">
                Your digital twin indicates excellent health trends
              </p>
            </div>
            <div className="w-48 h-48 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white relative">
              <div className="absolute inset-4 rounded-full bg-white/20 backdrop-blur-sm"></div>
              <div className="relative">
                <Bot className="h-24 w-24" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3D Visualization */}
      <Card className="apple-card">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center">
              <Eye className="h-5 w-5 mr-2" />
              Interactive Health Model
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setUse3DViewer(!use3DViewer)
                  setSelectedSystem(null)
                }}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  use3DViewer
                    ? 'bg-gradient-to-r from-teal-600 to-teal-500 text-white'
                    : 'border border-gray-300 bg-white hover:bg-gray-50'
                }`}
              >
                {use3DViewer ? '3D Mode' : '2D Mode'}
              </button>
              {!use3DViewer && (
                <>
                  <button
                    onClick={rotateModel}
                    className="px-4 py-2 rounded-md text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 flex items-center"
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    Rotate
                  </button>
                  <button
                    onClick={() => setShowFullModel(!showFullModel)}
                    className="px-4 py-2 rounded-md text-sm font-medium border border-gray-300 bg-white hover:bg-gray-50 flex items-center"
                  >
                    <Maximize2 className="h-4 w-4 mr-1" />
                    {showFullModel ? 'Collapse' : 'Expand'}
                  </button>
                </>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {use3DViewer ? (
            /* Three.js + OpenUSD Digital Twin Viewer */
            <DigitalTwinViewer
              onPatientSelect={(patientData) => {
                console.log('Patient data:', patientData)
              }}
            ></DigitalTwinViewer>
          ) : (
            /* SVG 2D Visualization */
            <div
              className={`bg-gradient-to-br from-slate-900 to-blue-900 rounded-lg relative overflow-hidden transition-all duration-500 ${showFullModel ? 'aspect-square' : 'aspect-video'}`}
              onClick={() => setSelectedSystem(null)}
            >
              {/* Interactive body visualization */}
              <div
                className="absolute inset-0 flex items-center justify-center transition-transform duration-700"
                style={{ transform: `rotateY(${modelRotation}deg)` }}
                onClick={() => setSelectedSystem(null)}
              >
                <div className="relative">
                  {/* Stylized human body outline */}
                  <svg viewBox="0 0 200 400" className="w-32 h-64 md:w-48 md:h-96">
                    {/* Body outline */}
                    <ellipse cx="100" cy="40" rx="30" ry="35" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M70 75 L60 180 L80 180 L85 140 L100 145 L115 140 L120 180 L140 180 L130 75" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M60 180 L55 300 L75 300 L85 200" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M140 180 L145 300 L125 300 L115 200" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M55 300 L50 380 L70 380 L75 300" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M145 300 L150 380 L130 380 L125 300" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    {/* Arms */}
                    <path d="M70 85 L30 160 L35 165 L75 95" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />
                    <path d="M130 85 L170 160 L165 165 L125 95" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2" />

                    {/* Interactive system indicators */}
                    {/* Brain - Nervous System */}
                    <circle
                      cx="100" cy="35" r="15"
                      fill={selectedSystem === 'nervous' ? 'rgba(168, 85, 247, 0.8)' : 'rgba(168, 85, 247, 0.3)'}
                      className="cursor-pointer transition-all hover:fill-purple-400"
                      onClick={(e) => { e.stopPropagation(); setSelectedSystem(selectedSystem === 'nervous' ? null : 'nervous'); }}
                    />
                    {/* Heart - Cardiovascular */}
                    <circle
                      cx="95" cy="100" r="12"
                      fill={selectedSystem === 'cardiovascular' ? 'rgba(239, 68, 68, 0.8)' : 'rgba(239, 68, 68, 0.3)'}
                      className="cursor-pointer transition-all hover:fill-red-400 animate-pulse"
                      onClick={(e) => { e.stopPropagation(); setSelectedSystem(selectedSystem === 'cardiovascular' ? null : 'cardiovascular'); }}
                    />
                    {/* Immune System - Thymus area */}
                    <circle
                      cx="100" cy="120" r="10"
                      fill={selectedSystem === 'immune' ? 'rgba(59, 130, 246, 0.8)' : 'rgba(59, 130, 246, 0.3)'}
                      className="cursor-pointer transition-all hover:fill-blue-400"
                      onClick={(e) => { e.stopPropagation(); setSelectedSystem(selectedSystem === 'immune' ? null : 'immune'); }}
                    />
                    {/* Metabolic - Stomach area */}
                    <circle
                      cx="100" cy="155" r="14"
                      fill={selectedSystem === 'metabolic' ? 'rgba(34, 197, 94, 0.8)' : 'rgba(34, 197, 94, 0.3)'}
                      className="cursor-pointer transition-all hover:fill-green-400"
                      onClick={(e) => { e.stopPropagation(); setSelectedSystem(selectedSystem === 'metabolic' ? null : 'metabolic'); }}
                    />
                  </svg>

                  {/* System label */}
                  {selectedSystem && (
                    <div
                      className="absolute -right-4 top-1/2 -translate-y-1/2 bg-white/20 backdrop-blur-md rounded-lg p-3 pr-8 text-white text-sm max-w-52 shadow-lg cursor-pointer hover:bg-white/30 transition-colors"
                      onClick={() => setSelectedSystem(null)}
                      title="Click to close"
                    >
                      <button
                        onClick={(e) => { e.stopPropagation(); setSelectedSystem(null); }}
                        className="absolute top-1 right-1 w-6 h-6 bg-white/30 hover:bg-white/50 rounded-full flex items-center justify-center text-white transition-colors"
                        aria-label="Close"
                      >
                        <X className="w-4 h-4" />
                      </button>
                      <p className="font-semibold">{healthSystems.find(s => s.id === selectedSystem)?.name}</p>
                      <p className="text-xs mt-1 text-gray-200">{healthSystems.find(s => s.id === selectedSystem)?.description}</p>
                      <p className="text-xs mt-2 text-gray-300 italic">Click to dismiss</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Animated particles effect */}
              <div className="absolute inset-0 opacity-30 pointer-events-none">
                {Array.from({ length: 30 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
                    style={{
                      left: `${10 + Math.random() * 80}%`,
                      top: `${10 + Math.random() * 80}%`,
                      animationDelay: `${Math.random() * 2}s`,
                    }}
                  ></div>
                ))}
              </div>

              {/* Instructions overlay */}
              <div className="absolute bottom-4 left-4 text-white/70 text-xs">
                Click on body regions to explore systems
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Status Overview */}
      <Card className="apple-card">
        <CardHeader>
          <CardTitle>Body Systems Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {healthSystems.map((system) => (
              <div
                key={system.id}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  selectedSystem === system.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedSystem(selectedSystem === system.id ? null : system.id)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <system.icon className={`h-6 w-6 mr-3 ${system.color}`} />
                    <h4 className="font-medium">{system.name}</h4>
                  </div>
                  <span className="text-2xl font-bold">{system.status}%</span>
                </div>
                <Progress value={system.status} className="h-2" />
                <div className="mt-2 flex items-center text-sm text-gray-600">
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                  <span>Trending positive</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Analysis Tabs */}
      <Tabs defaultValue="predictions" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="predictions" className="space-y-6">
          <Card className="apple-card">
            <CardHeader>
              <CardTitle>Health Predictions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border-l-4 border-green-500 bg-green-50 p-4 rounded">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-green-900">Positive Outlook</h4>
                      <p className="text-sm text-green-700 mt-1">
                        Based on current trends, your CD4 count is predicted to remain in healthy range
                      </p>
                    </div>
                    <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">95% confidence</span>
                  </div>
                </div>

                <div className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-blue-900">Weight Goal Progress</h4>
                      <p className="text-sm text-blue-700 mt-1">
                        At current pace, you're likely to reach your target weight in 6 weeks
                      </p>
                    </div>
                    <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">88% confidence</span>
                  </div>
                </div>

                <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4 rounded">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-yellow-900">Sleep Pattern Alert</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        Consider improving sleep consistency to optimize immune function
                      </p>
                    </div>
                    <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded">72% confidence</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card className="apple-card">
            <CardHeader>
              <CardTitle>30-Day Health Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Placeholder for charts - in production, use recharts or similar */}
                <div>
                  <h4 className="font-medium mb-3">Medication Adherence</h4>
                  <div className="h-32 bg-gradient-to-r from-green-100 to-green-200 rounded-lg flex items-end justify-around p-4">
                    {Array.from({ length: 30 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-teal-600 rounded-t"
                        style={{ height: `${70 + Math.random() * 30}%` }}
                      ></div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Average: 95% • Trend: ↗ Improving</p>
                </div>

                <div>
                  <h4 className="font-medium mb-3">Activity Level</h4>
                  <div className="h-32 bg-gradient-to-r from-blue-100 to-blue-200 rounded-lg flex items-end justify-around p-4">
                    {Array.from({ length: 30 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-blue-600 rounded-t"
                        style={{ height: `${50 + Math.random() * 50}%` }}
                      ></div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Average: 8,432 steps • Trend: → Stable</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card className="apple-card">
            <CardHeader>
              <CardTitle>Personalized Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg">
                  <Activity className="h-6 w-6 text-blue-500 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-medium">Increase Cardiovascular Activity</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Adding 15 minutes of moderate exercise could improve your cardiovascular score by 5%
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      View Exercise Plans
                    </Button>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-4 bg-purple-50 rounded-lg">
                  <Brain className="h-6 w-6 text-purple-500 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-medium">Mindfulness Practice</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Daily meditation could help reduce stress markers and improve overall wellness
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      Start Guided Meditation
                    </Button>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-4 bg-green-50 rounded-lg">
                  <Heart className="h-6 w-6 text-green-500 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-medium">Nutrition Optimization</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Your digital twin suggests increasing vitamin D intake for immune support
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      View Nutrition Guide
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* AI Insights */}
      <Card className="apple-card border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bot className="h-5 w-5 mr-2 text-purple-600" />
            AI-Powered Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700 mb-4">
            Your digital twin has analyzed 30 days of health data and identified key patterns that could
            enhance your wellness journey. The simulation suggests maintaining current medication adherence
            while focusing on sleep quality and stress management for optimal outcomes.
          </p>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setShowChat(true)}
          >
            <Bot className="h-4 w-4 mr-2" />
            Chat with AI Health Assistant
          </Button>
        </CardContent>
      </Card>

      {/* AI Chat Modal */}
      {showChat && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl h-[600px] flex flex-col">
            <CardHeader className="flex-shrink-0 border-b">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Bot className="h-5 w-5 mr-2 text-purple-600" />
                  AI Health Assistant
                </span>
                <Button variant="ghost" size="sm" onClick={() => setShowChat(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </CardTitle>
              <p className="text-sm text-gray-500">Ask questions about your Digital Twin data and health insights</p>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              <ScrollArea className="flex-1 px-6">
                <div className="space-y-4 py-4">
                  {chatMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start gap-3 ${
                        message.role === 'user' ? 'flex-row-reverse' : ''
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.role === 'user'
                            ? 'bg-teal-600'
                            : 'bg-gradient-to-br from-purple-500 to-pink-500'
                        }`}
                      >
                        {message.role === 'user' ? (
                          <User className="h-4 w-4 text-white" />
                        ) : (
                          <Bot className="h-4 w-4 text-white" />
                        )}
                      </div>
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-teal-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs mt-1 opacity-70">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-gray-100 rounded-lg p-3">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              <div className="p-4 border-t flex-shrink-0">
                <div className="flex gap-2">
                  <Input
                    placeholder="Ask about your health metrics, trends, or recommendations..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={handleChatKeyPress}
                    disabled={chatLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendChat}
                    disabled={chatLoading || !chatInput.trim()}
                    className="bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-700 hover:to-teal-600"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex gap-2 mt-2 flex-wrap">
                  <button
                    onClick={() => setChatInput('How is my immune system?')}
                    className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition"
                  >
                    Immune status
                  </button>
                  <button
                    onClick={() => setChatInput('Tell me about my cardiovascular health')}
                    className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full hover:bg-red-200 transition"
                  >
                    Heart health
                  </button>
                  <button
                    onClick={() => setChatInput('How can I improve my sleep?')}
                    className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200 transition"
                  >
                    Sleep tips
                  </button>
                  <button
                    onClick={() => setChatInput('How is my medication adherence?')}
                    className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition"
                  >
                    Medication
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
