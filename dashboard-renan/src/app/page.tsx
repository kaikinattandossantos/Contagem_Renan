"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Users, Newspaper, Calendar, ArrowUp, AlertCircle, ExternalLink, Heart } from "lucide-react"
import {
  Line, LineChart, Bar, BarChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from "recharts"

// Backup para caso a API falhe na apresentação
const backupDailyData = [
  { date: "01/12", followers: 45200, growth: 120 },
  { date: "30/12", followers: 56580, growth: 430 },
]

export default function PoliticalDashboard() {
  const [timeRange, setTimeRange] = useState<"daily" | "weekly">("daily")
  
  // Estados
  const [chartData, setChartData] = useState<any[]>(backupDailyData)
  const [newsData, setNewsData] = useState<any[]>([])
  const [currentFollowers, setCurrentFollowers] = useState(0)
  const [loading, setLoading] = useState(true)
  const [usingBackup, setUsingBackup] = useState(false)

  const USERNAME = "renansantosmbl" 

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch(`https://contagemrenan-production.up.railway.app/dashboard/${USERNAME}`)
        if (!response.ok) throw new Error("API Offline")
        
        const data = await response.json()
        
        // Atualiza Gráfico
        if (data.daily_data && data.daily_data.length > 0) {
            setChartData(data.daily_data)
        }
        
        // Atualiza KPI
        if (data.current_followers) setCurrentFollowers(data.current_followers)

        // Atualiza Notícias/Posts
        if (data.top_news) setNewsData(data.top_news)

      } catch (error) {
        console.warn("Usando backup...")
        setUsingBackup(true)
        setCurrentFollowers(56580)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <div className="flex h-screen items-center justify-center text-slate-500 font-medium">Carregando QG Digital...</div>

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans">
      <div className="container mx-auto space-y-6">
        
        {/* Cabeçalho */}
        <div className="flex justify-between items-start">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Monitoramento: @{USERNAME}</h1>
                <p className="text-slate-500">Inteligência de dados e impacto</p>
            </div>
            {usingBackup && (
                <Badge variant="destructive" className="gap-2">
                    <AlertCircle className="w-4 h-4"/> API Offline
                </Badge>
            )}
        </div>

        {/* KPIs */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">Seguidores Atuais</CardTitle>
              <Users className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{currentFollowers.toLocaleString("pt-BR")}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">Impacto Recente</CardTitle>
              <Heart className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">
                {newsData.length > 0 ? newsData[0].impact.toLocaleString("pt-BR") : "0"}
              </div>
              <p className="text-xs text-slate-500 mt-1">Likes no último post</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">Posts Rastreados</CardTitle>
              <Newspaper className="h-4 w-4 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{newsData.length}</div>
            </CardContent>
          </Card>
        </div>

        {/* Gráfico */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Curva de Crescimento</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis domain={['auto', 'auto']} stroke="#64748b" fontSize={12} tickFormatter={(val) => `${(val/1000).toFixed(0)}k`} />
                  <Tooltip />
                  <Area type="monotone" dataKey="followers" stroke="#2563eb" fill="url(#colorFollowers)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Lista de Posts (Substituindo Eventos de Impacto) */}
        <Card>
            <CardHeader>
                <CardTitle>Últimas Atualizações (Instagram)</CardTitle>
                <CardDescription>O que está gerando engajamento agora</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {newsData.length === 0 ? (
                        <p className="text-slate-500 text-center py-4">Nenhum post recente capturado ainda.</p>
                    ) : (
                        newsData.map((news) => (
                            <div key={news.id} className="flex items-start justify-between p-4 border rounded-lg bg-white hover:bg-slate-50 transition-colors">
                                <div className="space-y-1 max-w-[80%]">
                                    <h4 className="font-semibold text-sm text-slate-900 line-clamp-1">{news.title}</h4>
                                    <p className="text-xs text-slate-500 line-clamp-2">{news.description}</p>
                                    <div className="flex gap-2 mt-2">
                                        <Badge variant="secondary" className="text-xs">{news.date}</Badge>
                                        <a href={news.url} target="_blank" className="text-xs text-blue-600 flex items-center hover:underline">
                                            Ver no Instagram <ExternalLink className="w-3 h-3 ml-1"/>
                                        </a>
                                    </div>
                                </div>
                                <div className="text-center min-w-[60px]">
                                    <span className="block font-bold text-slate-900">{news.impact.toLocaleString("pt-BR")}</span>
                                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Likes</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  )
}