"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Users, Newspaper, Calendar, ArrowUp, AlertCircle } from "lucide-react"
import {
  Line, LineChart, Bar, BarChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from "recharts"

// --- DADOS DE BACKUP (Para garantir que a apresentação não falhe) ---
const backupDailyData = [
  { date: "01/12", followers: 45200, growth: 120 },
  { date: "15/12", followers: 51100, growth: 450 },
  { date: "26/12", followers: 54320, growth: 870, event: "Entrevista Nacional" },
  { date: "30/12", followers: 56580, growth: 430 },
]

const topNews = [
  {
    id: 1,
    title: "Proposta de Reforma na Educação",
    date: "12-13 Dez",
    impact: "+1,730",
    percentage: "+3.5%",
    description: "Apresentação de proposta inovadora para educação pública",
  },
  {
    id: 2,
    title: "Entrevista no Programa Nacional",
    date: "26-27 Dez",
    impact: "+1,650",
    percentage: "+3.0%",
    description: "Participação em entrevista de grande audiência",
  },
]

export default function PoliticalDashboard() {
  const [timeRange, setTimeRange] = useState<"daily" | "weekly" | "monthly">("daily")
  
  // Estados Reais
  const [chartData, setChartData] = useState<any[]>(backupDailyData)
  const [currentFollowers, setCurrentFollowers] = useState(0)
  const [loading, setLoading] = useState(true)
  const [usingBackup, setUsingBackup] = useState(false)

  // Configuração
  const USERNAME = "renansantosmbl" 

  useEffect(() => {
    async function fetchData() {
      try {
        // Tenta conectar na API Python local
        const response = await fetch(`http://127.0.0.1:8000/dashboard/${USERNAME}`)
        
        if (!response.ok) throw new Error("Falha na API")
        
        const data = await response.json()
        
        if (data.daily_data && data.daily_data.length > 0) {
            setChartData(data.daily_data)
            setCurrentFollowers(data.current_followers)
        } else {
            // Se a API retornar vazio (primeiro dia), usa backup
            setUsingBackup(true)
            setCurrentFollowers(56580) // Valor mockado
        }
      } catch (error) {
        console.warn("⚠️ API Python offline ou erro de conexão. Usando dados de backup.")
        setUsingBackup(true)
        setCurrentFollowers(56580) // Valor mockado
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
      return <div className="flex h-screen items-center justify-center text-slate-500">Carregando inteligência de dados...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-6">
      <div className="container mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
            <div className="space-y-2">
            <h1 className="text-4xl font-bold text-slate-900">QG Digital: @{USERNAME}</h1>
            <p className="text-slate-600 text-lg">Monitoramento estratégico de crescimento e impacto</p>
            </div>
            {usingBackup && (
                <Badge variant="destructive" className="flex gap-2">
                    <AlertCircle className="w-4 h-4"/> Modo Demonstração (API Offline)
                </Badge>
            )}
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total de Seguidores</CardTitle>
              <Users className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{currentFollowers.toLocaleString("pt-BR")}</div>
              <p className="text-xs text-slate-500 mt-1">Atualizado em tempo real</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Média Diária (Est.)</CardTitle>
              <Calendar className="h-4 w-4 text-violet-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">+380</div>
              <p className="text-xs text-slate-500 mt-1">Novos apoiadores/dia</p>
            </CardContent>
          </Card>
          
          {/* Adicione mais cards conforme necessário */}
        </div>

        {/* Main Chart */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-slate-900">Evolução da Base</CardTitle>
                <CardDescription>Correlação entre eventos e crescimento</CardDescription>
              </div>
              <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as any)} className="w-auto">
                <TabsList>
                  <TabsTrigger value="daily">Diário</TabsTrigger>
                  <TabsTrigger value="weekly">Semanal</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis domain={['auto', 'auto']} stroke="#64748b" fontSize={12} tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "white", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    formatter={(value: any, name: string) => [value.toLocaleString("pt-BR"), name === "followers" ? "Seguidores" : "Crescimento"]}
                  />
                  <Area type="monotone" dataKey="followers" stroke="#3b82f6" strokeWidth={2} fill="url(#colorFollowers)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* News Section (Mantida estática por enquanto pois não temos scraping de notícias ainda) */}
        <Card className="border-slate-200 shadow-sm">
            <CardHeader>
                <CardTitle>Eventos de Impacto</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {topNews.map((news, i) => (
                        <div key={i} className="flex items-center justify-between p-4 bg-white border rounded-lg">
                            <div>
                                <h3 className="font-bold">{news.title}</h3>
                                <p className="text-sm text-gray-500">{news.description}</p>
                            </div>
                            <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">{news.impact}</Badge>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  )
}