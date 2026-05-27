/**
 * 竞品分析 v4 - 商业级
 * 价格历史趋势 + 调价规则引擎 + 竞品对标分析 + 自动预警
 * + 趋势分析(价格走势/市场格局/竞品评分) + 批量操作 + 价格分布图
 */
import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { generateCompetitors, PLATFORMS } from '../../utils/mock';
import './Competitors.css';

const PRICE_RULES = [
  { id: 1, name: '低价跟随策略', desc: '竞品降价时，我方自动跟进降价5%', condition: '竞品价 < 我方价', action: '设为竞品价 × 0.95', enabled: true },
  { id: 2, name: '高价截流策略', desc: '竞品涨价时，我方保持原价截取流量', condition: '竞品价 > 我方价', action: '保持原价不变', enabled: false },
  { id: 3, name: '利润保护策略', desc: '当利润率低于15%时，不自动降价', condition: '利润率 < 15%', action: '暂停自动调价', enabled: true },
  { id: 4, name: '库存清仓策略', desc: '库存>200且30天无销量时，自动降价20%', condition: '库存>200 & 30天销量=0', action: '自动降价20%', enabled: false },
];

// 生成价格历史数据(最近30天)
const generatePriceHistory = (basePrice, volatility = 0.05) => {
  const history = [];
  let price = basePrice * (1 - volatility * 2);
  for (let i = 29; i >= 0; i--) {
    const change = (Math.random() - 0.48) * basePrice * volatility;
    price = Math.max(basePrice * 0.7, Math.min(basePrice * 1.3, price + change));
    history.push({
      date: new Date(Date.now() - i * 86400000).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }),
      theirPrice: +price.toFixed(2),
      ourPrice: +(price * (0.92 + Math.random() * 0.16)).toFixed(2),
    });
  }
  return history;
};

// 迷你折线图(SVG)
const MiniSparkline = ({ data, width = 120, height = 32, color = '#165DFF', secondColor }) => {
  if (!data || data.length < 2) return null;
  const allVals = data.flatMap(d => [d.theirPrice || d, ...(d.ourPrice ? [d.ourPrice] : [])]);
  const min = Math.min(...allVals);
  const max = Math.max(...allVals);
  const range = max - min || 1;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((typeof d === 'number' ? d : d.theirPrice) - min) / range * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  const ourPoints = secondColor && data[0]?.ourPrice ? data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - (d.ourPrice - min) / range * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ') : null;

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
      {ourPoints && <polyline points={ourPoints} fill="none" stroke={secondColor} strokeWidth="1.5" strokeDasharray="3,2" strokeLinejoin="round" />}
    </svg>
  );
};

// 柱状分布图(SVG)
const BarDistribution = ({ values, width = 200, height = 60, color = '#165DFF' }) => {
  if (!values || values.length === 0) return null;
  const max = Math.max(...values);
  const barW = Math.max(4, (width - values.length * 2) / values.length);
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {values.map((v, i) => {
        const barH = max > 0 ? (v / max) * (height - 8) : 0;
        return (
          <rect key={i} x={i * (barW + 2)} y={height - barH - 2} width={barW} height={barH}
            fill={color} opacity={0.7 + (v / max) * 0.3} rx="1" />
        );
      })}
    </svg>
  );
};

export default function Competitors() {
  const [competitors, setCompetitors] = useState(() => generateCompetitors(20));
  const [platform, setPlatform] = useState('all');
  const [keyword, setKeyword] = useState('');
  const [sortBy, setSortBy] = useState('priceDiff');
  const [sortDir, setSortDir] = useState('desc');
  const [detailItem, setDetailItem] = useState(null);
  const [adjustItem, setAdjustItem] = useState(null);
  const [adjustPrice, setAdjustPrice] = useState('');
  const [adjustReason, setAdjustReason] = useState('');
  const [showAddMonitor, setShowAddMonitor] = useState(false);
  const [showRules, setShowRules] = useState(false);
  const [toast, setToast] = useState('');
  const [newMonitor, setNewMonitor] = useState({ name: '', platform: 'douyin', theirPrice: '', ourPrice: '', competitor: '' });
  const [priceHistory, setPriceHistory] = useState([]);
  const [rules, setRules] = useState(PRICE_RULES);
  const [analysisMode, setAnalysisMode] = useState('overview'); // overview | pricing | alerts | trends
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [priceHistories] = useState(() => {
    const map = {};
    competitors.forEach(c => { map[c.id] = generatePriceHistory(c.theirPrice); });
    return map;
  });
  const [trendMetric, setTrendMetric] = useState('price'); // price | sales | rating

  const filtered = useMemo(() => {
    let list = competitors;
    if (platform !== 'all') list = list.filter(c => c.platform === platform);
    if (keyword) {
      const kw = keyword.toLowerCase();
      list = list.filter(c => c.name.toLowerCase().includes(kw) || c.competitor.toLowerCase().includes(kw));
    }
    return [...list].sort((a, b) => {
      const mul = sortDir === 'desc' ? -1 : 1;
      return (a[sortBy] - b[sortBy]) * mul;
    });
  }, [competitors, platform, keyword, sortBy, sortDir]);

  const showToast = useCallback((msg) => { setToast(msg); setTimeout(() => setToast(''), 3000); }, []);

  const handleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortBy(field); setSortDir('desc'); }
  };

  // 批量选择
  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };
  const toggleSelectAll = () => {
    if (selectedIds.size === filtered.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(filtered.map(c => c.id)));
  };

  const recordPriceChange = (item, oldPrice, newPrice, reason) => {
    setPriceHistory(prev => [{
      time: new Date().toLocaleString('zh-CN'),
      name: item.name,
      platform: PLATFORMS.find(p => p.key === item.platform)?.name,
      oldPrice: oldPrice.toFixed(2),
      newPrice: newPrice.toFixed(2),
      diff: ((newPrice - oldPrice) / oldPrice * 100).toFixed(1),
      reason: reason || '手动调价',
      operator: '马晓倩',
    }, ...prev].slice(0, 50));
  };

  const handleApplySuggestion = (item, customPrice) => {
    const newPrice = customPrice || item.theirPrice * 0.95;
    const oldPrice = item.ourPrice;
    setCompetitors(prev => prev.map(c => c.id === item.id ? { ...c, ourPrice: newPrice, priceDiff: ((newPrice - c.theirPrice) / c.theirPrice * 100).toFixed(1) } : c));
    recordPriceChange(item, oldPrice, newPrice, customPrice ? '手动调价' : '应用建议价');
    showToast(`${item.name} 价格已从 ¥${oldPrice.toFixed(2)} 调整为 ¥${newPrice.toFixed(2)}`);
  };

  const handleAdjustPrice = () => {
    if (!adjustItem || !adjustPrice) return;
    const newPrice = parseFloat(adjustPrice);
    if (isNaN(newPrice) || newPrice <= 0) { showToast('请输入有效价格'); return; }
    handleApplySuggestion(adjustItem, newPrice);
    setAdjustItem(null); setAdjustPrice(''); setAdjustReason('');
  };

  // 批量调价
  const handleBatchAdjust = (strategy) => {
    const items = competitors.filter(c => selectedIds.has(c.id));
    let count = 0;
    setCompetitors(prev => prev.map(c => {
      if (!selectedIds.has(c.id)) return c;
      let newPrice;
      if (strategy === 'follow') {
        newPrice = c.theirPrice * 0.95;
      } else if (strategy === 'match') {
        newPrice = c.theirPrice;
      } else {
        return c;
      }
      if (Math.abs(newPrice - c.ourPrice) < 0.01) return c;
      recordPriceChange(c, c.ourPrice, newPrice, strategy === 'follow' ? '批量跟随' : '批量持平');
      count++;
      return { ...c, ourPrice: +newPrice.toFixed(2), priceDiff: ((newPrice - c.theirPrice) / c.theirPrice * 100).toFixed(1) };
    }));
    showToast(`批量${strategy === 'follow' ? '跟随' : '持平'}: ${count} 个商品已调价`);
    setSelectedIds(new Set());
  };

  const handleBatchApplyRule = (rule) => {
    let count = 0;
    setCompetitors(prev => prev.map(c => {
      const margin = (c.ourPrice - c.theirPrice) / c.ourPrice;
      if (rule.id === 1 && c.theirPrice < c.ourPrice && margin > 0.15) {
        const newPrice = c.theirPrice * 0.95;
        recordPriceChange(c, c.ourPrice, newPrice, '低价跟随策略');
        count++;
        return { ...c, ourPrice: newPrice, priceDiff: ((newPrice - c.theirPrice) / c.theirPrice * 100).toFixed(1) };
      }
      return c;
    }));
    showToast(`「${rule.name}」已对 ${count} 个商品生效`);
  };

  const handleToggleRule = (ruleId) => {
    setRules(prev => prev.map(r => r.id === ruleId ? { ...r, enabled: !r.enabled } : r));
  };

  const handleExport = () => {
    const headers = ['商品名称', '竞品店铺', '平台', '竞品价格', '我方价格', '价差%', '利润率%', '竞品销量', '我方销量', '竞品评分', '状态'];
    const rows = filtered.map(c => {
      const margin = ((c.ourPrice - c.ourPrice * 0.4) / c.ourPrice * 100).toFixed(1);
      const status = parseFloat(c.priceDiff) < 0 ? '有优势' : parseFloat(c.priceDiff) > 5 ? '需关注' : '正常';
      return [c.name, c.competitor, PLATFORMS.find(p => p.key === c.platform)?.name, c.theirPrice, c.ourPrice, c.priceDiff + '%', margin + '%', c.theirSales, c.ourSales, c.theirRating, status];
    });
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `竞品分析_${new Date().toISOString().slice(0,10)}.csv`; a.click();
    URL.revokeObjectURL(url);
    showToast('竞品数据已导出');
  };

  const handleAddMonitor = () => {
    if (!newMonitor.name || !newMonitor.theirPrice || !newMonitor.ourPrice) { showToast('请填写必要信息'); return; }
    const item = {
      id: `comp_${Date.now()}`,
      name: newMonitor.name, platform: newMonitor.platform,
      competitor: newMonitor.competitor || '未知店铺',
      theirPrice: parseFloat(newMonitor.theirPrice), ourPrice: parseFloat(newMonitor.ourPrice),
      priceDiff: (((parseFloat(newMonitor.ourPrice) - parseFloat(newMonitor.theirPrice)) / parseFloat(newMonitor.theirPrice)) * 100).toFixed(1),
      theirSales: 0, ourSales: 0,
      theirRating: '-', updatedAt: new Date().toISOString(),
    };
    setCompetitors(prev => [item, ...prev]);
    setShowAddMonitor(false);
    setNewMonitor({ name: '', platform: 'douyin', theirPrice: '', ourPrice: '', competitor: '' });
    showToast('竞品监控添加成功');
  };

  const getPlatformInfo = (key) => PLATFORMS.find(p => p.key === key) || { name: key, icon: '📦' };
  const avgDiff = competitors.length ? (competitors.reduce((s, c) => s + parseFloat(c.priceDiff), 0) / competitors.length).toFixed(1) : 0;
  const cheaperCount = competitors.filter(c => parseFloat(c.priceDiff) < 0).length;
  const expensiveCount = competitors.filter(c => parseFloat(c.priceDiff) > 0).length;
  const criticalCount = competitors.filter(c => parseFloat(c.priceDiff) > 10).length;
  const totalOurSales = competitors.reduce((s, c) => s + (c.ourSales || 0), 0);
  const totalTheirSales = competitors.reduce((s, c) => s + c.theirSales, 0);

  // 竞品强度评分(综合价格、销量、评分)
  const strengthScores = useMemo(() => {
    return competitors.map(c => {
      const priceScore = Math.max(0, 100 - Math.abs(parseFloat(c.priceDiff)) * 3);
      const salesScore = Math.min(100, (c.ourSales / Math.max(c.theirSales, 1)) * 100);
      const ratingScore = (c.ourSales > 0 ? 4.0 : 0) / 5 * 100; // 模拟我方评分
      return {
        ...c,
        priceScore: +priceScore.toFixed(0),
        salesScore: +salesScore.toFixed(0),
        ratingScore: +ratingScore.toFixed(0),
        totalScore: +((priceScore * 0.4 + salesScore * 0.35 + ratingScore * 0.25)).toFixed(0),
      };
    }).sort((a, b) => b.totalScore - a.totalScore);
  }, [competitors]);

  // 价格分布区间
  const priceDistribution = useMemo(() => {
    const buckets = [0, 0, 0, 0, 0]; // <-20%, -20~-5%, -5~5%, 5~20%, >20%
    competitors.forEach(c => {
      const d = parseFloat(c.priceDiff);
      if (d < -20) buckets[0]++;
      else if (d < -5) buckets[1]++;
      else if (d < 5) buckets[2]++;
      else if (d < 20) buckets[3]++;
      else buckets[4]++;
    });
    return buckets;
  }, [competitors]);

  // 按平台统计
  const platformStats = useMemo(() => {
    const stats = {};
    competitors.forEach(c => {
      if (!stats[c.platform]) stats[c.platform] = { count: 0, totalDiff: 0, cheaper: 0 };
      stats[c.platform].count++;
      stats[c.platform].totalDiff += parseFloat(c.priceDiff);
      if (parseFloat(c.priceDiff) < 0) stats[c.platform].cheaper++;
    });
    return Object.entries(stats).map(([key, val]) => ({
      key,
      ...getPlatformInfo(key),
      count: val.count,
      avgDiff: (val.totalDiff / val.count).toFixed(1),
      cheaperRate: ((val.cheaper / val.count) * 100).toFixed(0),
    })).sort((a, b) => b.count - a.count);
  }, [competitors]);

  const SortIcon = ({ field }) => (
    <span style={{ marginLeft: 4, opacity: sortBy === field ? 1 : 0.3 }}>{sortBy === field ? (sortDir === 'desc' ? '↓' : '↑') : '↕'}</span>
  );
  const inputStyle = { width: '100%', padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 14, outline: 'none', marginBottom: 12 };

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="page-title">竞品分析</h2>
          <p className="page-desc">价格监控、调价策略、竞品对标分析、趋势洞察</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['overview', 'pricing', 'alerts', 'trends'].map(mode => {
            const labels = { overview: '📊 总览', pricing: '💰 调价策略', alerts: '🚨 预警', trends: '📈 趋势分析' };
            return (
              <button key={mode} className={`btn btn-sm ${analysisMode === mode ? 'btn-primary' : 'btn-default'}`}
                onClick={() => setAnalysisMode(mode)}>{labels[mode]}</button>
            );
          })}
        </div>
      </div>

      {/* 统计概览 */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-card-title">监控商品</div>
          <div className="stat-card-value" style={{ fontSize: 24 }}>{competitors.length}</div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>覆盖 {platformStats.length} 个平台</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">平均价差</div>
          <div className="stat-card-value" style={{ fontSize: 24, color: parseFloat(avgDiff) > 0 ? 'var(--danger)' : 'var(--success)' }}>
            {parseFloat(avgDiff) > 0 ? '+' : ''}{avgDiff}%
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{cheaperCount} 个有优势 / {expensiveCount} 个偏高</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">我方有优势</div>
          <div className="stat-card-value" style={{ fontSize: 24, color: 'var(--success)' }}>{cheaperCount}</div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>占比 {((cheaperCount / competitors.length) * 100).toFixed(0)}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">价格偏高(&gt;10%)</div>
          <div className="stat-card-value" style={{ fontSize: 24, color: 'var(--danger)' }}>{criticalCount}</div>
          <div style={{ fontSize: 11, color: criticalCount > 0 ? 'var(--danger)' : 'var(--text-3)', marginTop: 2 }}>{criticalCount > 0 ? '需及时处理' : '状态良好'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">销量对比</div>
          <div className="stat-card-value" style={{ fontSize: 20 }}>
            {totalOurSales.toLocaleString()} <span style={{ fontSize: 12, color: 'var(--text-3)' }}>vs</span> {totalTheirSales.toLocaleString()}
          </div>
          <div style={{ fontSize: 11, color: totalOurSales >= totalTheirSales ? 'var(--success)' : '#FF7D00', marginTop: 2 }}>
            {totalOurSales >= totalTheirSales ? '我方领先' : `差距 ${(totalTheirSales - totalOurSales).toLocaleString()}`}
          </div>
        </div>
      </div>

      {/* 总览模式 */}
      {analysisMode === 'overview' && (
        <>
          <div className="filter-bar">
            <input className="filter-input" placeholder="搜索商品名、竞品店铺..." value={keyword} onChange={e => setKeyword(e.target.value)} />
            <select className="filter-select" value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="all">全部平台</option>
              {PLATFORMS.map(p => <option key={p.key} value={p.key}>{p.icon} {p.name}</option>)}
            </select>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              {selectedIds.size > 0 && (
                <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '0 8px', background: 'var(--primary-light, #E8F3FF)', borderRadius: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--primary)' }}>已选 {selectedIds.size} 项</span>
                  <button className="btn btn-sm btn-primary" onClick={() => handleBatchAdjust('follow')}>批量跟随</button>
                  <button className="btn btn-sm btn-default" onClick={() => handleBatchAdjust('match')}>批量持平</button>
                </div>
              )}
              <button className="btn btn-default" onClick={handleExport}>📤 导出分析</button>
              <button className="btn btn-primary" onClick={() => setShowAddMonitor(true)}>➕ 添加监控</button>
            </div>
          </div>

          {/* 平台分布卡片 */}
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(platformStats.length, 5)}, 1fr)`, gap: 12, marginBottom: 16 }}>
            {platformStats.map(ps => (
              <div key={ps.key} className="card" style={{ padding: '12px 16px', cursor: 'pointer', border: platform === ps.key ? '2px solid var(--primary)' : undefined }}
                onClick={() => setPlatform(platform === ps.key ? 'all' : ps.key)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 500 }}>{ps.icon} {ps.name}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{ps.count}个</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                  <span style={{ fontSize: 12, color: parseFloat(ps.avgDiff) < 0 ? 'var(--success)' : 'var(--danger)' }}>
                    均差 {parseFloat(ps.avgDiff) > 0 ? '+' : ''}{ps.avgDiff}%
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--success)' }}>{ps.cheaperRate}%有优势</span>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead><tr>
                  <th style={{ width: 36 }}><input type="checkbox" checked={selectedIds.size === filtered.length && filtered.length > 0} onChange={toggleSelectAll} /></th>
                  <th>商品</th><th>竞品店铺</th><th>平台</th><th>竞品价</th><th>我方价</th>
                  <th onClick={() => handleSort('priceDiff')} style={{ cursor: 'pointer' }}>价差<SortIcon field="priceDiff" /></th>
                  <th>价格走势</th>
                  <th onClick={() => handleSort('theirSales')} style={{ cursor: 'pointer' }}>竞品销量<SortIcon field="theirSales" /></th>
                  <th>竞品评分</th><th>状态</th><th>操作</th>
                </tr></thead>
                <tbody>
                  {filtered.map(item => {
                    const plat = getPlatformInfo(item.platform);
                    const diff = parseFloat(item.priceDiff);
                    const status = diff > 10 ? { label: '需调价', color: 'var(--danger)' } : diff > 0 ? { label: '偏高', color: '#FF7D00' } : diff > -5 ? { label: '正常', color: 'var(--success)' } : { label: '有优势', color: '#165DFF' };
                    return (
                      <tr key={item.id} style={{ background: selectedIds.has(item.id) ? 'var(--primary-light, #E8F3FF)' : undefined }}>
                        <td><input type="checkbox" checked={selectedIds.has(item.id)} onChange={() => toggleSelect(item.id)} /></td>
                        <td style={{ fontWeight: 500 }}>{item.name}</td>
                        <td style={{ color: 'var(--text-2)' }}>{item.competitor}</td>
                        <td>{plat.icon} {plat.name}</td>
                        <td style={{ fontWeight: 600 }}>¥{item.theirPrice.toFixed(2)}</td>
                        <td style={{ fontWeight: 600 }}>¥{item.ourPrice.toFixed(2)}</td>
                        <td><span style={{ color: diff < 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>{diff > 0 ? '+' : ''}{diff}%</span></td>
                        <td><MiniSparkline data={priceHistories[item.id]} width={80} height={24} color={diff < 0 ? 'var(--success)' : 'var(--danger)'} /></td>
                        <td>{item.theirSales.toLocaleString()}</td>
                        <td><span style={{ color: '#FF7D00' }}>★</span> {item.theirRating}</td>
                        <td><span className="tag" style={{ background: status.color + '15', color: status.color }}>{status.label}</span></td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            <button className="btn btn-text btn-sm" onClick={() => { setAdjustItem(item); setAdjustPrice(item.ourPrice.toString()); }}>调价</button>
                            <button className="btn btn-text btn-sm" onClick={() => setDetailItem(item)}>详情</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* 调价策略模式 */}
      {analysisMode === 'pricing' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">⚙️ 调价规则引擎</span><span style={{ fontSize: 12, color: 'var(--text-3)' }}>自动调价策略配置</span></div>
            <div className="card-body" style={{ padding: 0 }}>
              {rules.map((rule, i) => (
                <div key={rule.id} style={{ display: 'flex', alignItems: 'center', padding: '14px 16px', borderBottom: i < rules.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500, marginBottom: 4 }}>{rule.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{rule.desc}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-4)', marginTop: 4 }}>条件: {rule.condition} → {rule.action}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <button className="btn btn-sm btn-primary" onClick={() => handleBatchApplyRule(rule)} disabled={!rule.enabled}>应用</button>
                    <div className={`switch ${rule.enabled ? 'on' : ''}`} onClick={() => handleToggleRule(rule.id)} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">💰 定价建议</span></div>
            <div className="card-body" style={{ padding: 0 }}>
              {filtered.filter(c => parseFloat(c.priceDiff) > 5).slice(0, 6).map(item => {
                const suggested = item.theirPrice * 0.95;
                const profitMargin = ((suggested - item.ourPrice * 0.4) / suggested * 100).toFixed(1);
                return (
                  <div key={item.id} style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500, marginBottom: 2 }}>{item.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
                        竞品 ¥{item.theirPrice.toFixed(2)} | 当前 ¥{item.ourPrice.toFixed(2)} | 建议 ¥{suggested.toFixed(2)}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', marginRight: 12 }}>
                      <div style={{ fontSize: 12, color: parseFloat(profitMargin) > 20 ? 'var(--success)' : 'var(--danger)' }}>利润率 {profitMargin}%</div>
                    </div>
                    <button className="btn btn-sm btn-primary" onClick={() => handleApplySuggestion(item, suggested)}>应用</button>
                  </div>
                );
              })}
              {filtered.filter(c => parseFloat(c.priceDiff) > 5).length === 0 && (
                <div style={{ padding: 40, textAlign: 'center', color: 'var(--success)' }}>✅ 所有商品价格合理</div>
              )}
            </div>
          </div>
          {/* 价格分布 */}
          <div className="card">
            <div className="card-header"><span className="card-title">📊 价差分布</span></div>
            <div className="card-body">
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', justifyContent: 'space-between' }}>
                {['<-20%', '-20~-5%', '-5~5%', '5~20%', '>20%'].map((label, i) => {
                  const colors = ['#165DFF', '#36CFC9', '#00B42A', '#FF7D00', '#F53F3F'];
                  const maxVal = Math.max(...priceDistribution, 1);
                  const barH = (priceDistribution[i] / maxVal) * 80;
                  return (
                    <div key={label} style={{ flex: 1, textAlign: 'center' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: colors[i], marginBottom: 4 }}>{priceDistribution[i]}</div>
                      <div style={{ height: 80, display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <div style={{ width: '60%', height: barH, background: colors[i], borderRadius: '4px 4px 0 0', minHeight: 4 }} />
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 4 }}>{label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          {/* 调价历史 */}
          {priceHistory.length > 0 && (
            <div className="card" style={{ gridColumn: '1/3' }}>
              <div className="card-header"><span className="card-title">📋 调价记录</span><span style={{ fontSize: 12, color: 'var(--text-3)' }}>{priceHistory.length}条记录</span></div>
              <table className="data-table">
                <thead><tr><th>时间</th><th>商品</th><th>平台</th><th>原价</th><th>新价</th><th>变动</th><th>原因</th><th>操作人</th></tr></thead>
                <tbody>
                  {priceHistory.slice(0, 10).map((h, i) => (
                    <tr key={i}>
                      <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{h.time}</td>
                      <td style={{ fontWeight: 500 }}>{h.name}</td>
                      <td>{h.platform}</td>
                      <td>¥{h.oldPrice}</td>
                      <td style={{ fontWeight: 600, color: 'var(--primary)' }}>¥{h.newPrice}</td>
                      <td style={{ color: parseFloat(h.diff) > 0 ? 'var(--danger)' : 'var(--success)' }}>{parseFloat(h.diff) > 0 ? '+' : ''}{h.diff}%</td>
                      <td style={{ fontSize: 12 }}>{h.reason}</td>
                      <td style={{ fontSize: 12, color: 'var(--text-3)' }}>{h.operator}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 预警模式 */}
      {analysisMode === 'alerts' && (
        <>
          {/* 预警统计 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              { label: '严重(>15%)', count: competitors.filter(c => parseFloat(c.priceDiff) > 15).length, color: '#F53F3F', icon: '🔴' },
              { label: '警告(10~15%)', count: competitors.filter(c => { const d = parseFloat(c.priceDiff); return d > 10 && d <= 15; }).length, color: '#FF7D00', icon: '🟠' },
              { label: '关注(5~10%)', count: competitors.filter(c => { const d = parseFloat(c.priceDiff); return d > 5 && d <= 10; }).length, color: '#FADB14', icon: '🟡' },
            ].map(item => (
              <div key={item.label} className="card" style={{ padding: '14px 16px', borderLeft: `3px solid ${item.color}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13 }}>{item.icon} {item.label}</span>
                  <span style={{ fontSize: 20, fontWeight: 700, color: item.color }}>{item.count}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">🚨 价格异常预警</span>
              <span style={{ fontSize: 12, color: 'var(--text-3)' }}>按价差严重程度排序</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {[...competitors].sort((a, b) => parseFloat(b.priceDiff) - parseFloat(a.priceDiff))
                .filter(c => parseFloat(c.priceDiff) > 5)
                .map((item, i, arr) => {
                  const diff = parseFloat(item.priceDiff);
                  const severity = diff > 15 ? { bg: '#FFF1F0', border: '#F53F3F', icon: '🔴', label: '严重' }
                    : diff > 10 ? { bg: '#FFF7E6', border: '#FF7D00', icon: '🟠', label: '警告' }
                    : { bg: '#FFFEF0', border: '#FADB14', icon: '🟡', label: '关注' };
                  return (
                    <div key={item.id} style={{ display: 'flex', alignItems: 'center', padding: '14px 16px', borderBottom: i < arr.length - 1 ? '1px solid var(--border)' : 'none', background: severity.bg }}>
                      <span style={{ fontSize: 20, marginRight: 12 }}>{severity.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500 }}>
                          {item.name}
                          <span className="tag" style={{ marginLeft: 8, fontSize: 11, background: severity.border + '20', color: severity.border }}>{severity.label}</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>
                          竞品「{item.competitor}」售价 ¥{item.theirPrice.toFixed(2)}，我方 ¥{item.ourPrice.toFixed(2)}，价差 <b style={{ color: severity.border }}>+{diff}%</b>
                        </div>
                      </div>
                      <MiniSparkline data={priceHistories[item.id]} width={80} height={24} color={severity.border} />
                      <div style={{ display: 'flex', gap: 8, marginLeft: 16 }}>
                        <button className="btn btn-sm btn-primary" onClick={() => handleApplySuggestion(item)}>一键跟随</button>
                        <button className="btn btn-sm btn-default" onClick={() => { setAdjustItem(item); setAdjustPrice(item.ourPrice.toString()); }}>手动调价</button>
                      </div>
                    </div>
                  );
                })}
              {competitors.filter(c => parseFloat(c.priceDiff) > 5).length === 0 && (
                <div style={{ padding: 48, textAlign: 'center', color: 'var(--success)', fontSize: 16 }}>✅ 无价格异常预警</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* 趋势分析模式 */}
      {analysisMode === 'trends' && (
        <>
          {/* 竞品强度排名 */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">🏆 竞品强度排名</span>
              <span style={{ fontSize: 12, color: 'var(--text-3)' }}>综合价格竞争力、销量比、评分</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {strengthScores.slice(0, 10).map((item, i) => (
                <div key={item.id} style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderBottom: i < 9 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: i < 3 ? ['#FFD700', '#C0C0C0', '#CD7F32'][i] : 'var(--bg-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: i < 3 ? '#fff' : 'var(--text-2)', marginRight: 12 }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500, marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name}</div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{getPlatformInfo(item.platform).icon} {item.competitor}</span>
                    </div>
                  </div>
                  {/* 评分维度 */}
                  <div style={{ display: 'flex', gap: 12, marginRight: 16 }}>
                    {[
                      { label: '价格', score: item.priceScore, color: item.priceScore > 70 ? 'var(--success)' : item.priceScore > 40 ? '#FF7D00' : 'var(--danger)' },
                      { label: '销量', score: item.salesScore, color: item.salesScore > 70 ? 'var(--success)' : item.salesScore > 40 ? '#FF7D00' : 'var(--danger)' },
                      { label: '综合', score: item.totalScore, color: 'var(--primary)' },
                    ].map(dim => (
                      <div key={dim.label} style={{ textAlign: 'center', minWidth: 40 }}>
                        <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 2 }}>{dim.label}</div>
                        <div style={{ fontSize: 14, fontWeight: 600, color: dim.color }}>{dim.score}</div>
                      </div>
                    ))}
                  </div>
                  {/* 迷你进度条 */}
                  <div style={{ width: 80, height: 6, background: 'var(--bg-2)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${item.totalScore}%`, height: '100%', background: 'var(--primary)', borderRadius: 3 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 价格走势对比 */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <span className="card-title">📈 价格走势对比(近30天)</span>
              <div style={{ display: 'flex', gap: 4 }}>
                {['price', 'sales', 'rating'].map(m => (
                  <button key={m} className={`btn btn-xs ${trendMetric === m ? 'btn-primary' : 'btn-default'}`}
                    onClick={() => setTrendMetric(m)}>
                    {{ price: '价格', sales: '销量', rating: '评分' }[m]}
                  </button>
                ))}
              </div>
            </div>
            <div className="card-body">
              {trendMetric === 'price' && (
                <div>
                  {/* 大尺寸SVG图表 */}
                  {(() => {
                    const top5 = competitors.slice(0, 5);
                    const allData = top5.flatMap(c => priceHistories[c.id] || []);
                    if (allData.length === 0) return <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-3)' }}>暂无数据</div>;
                    const allPrices = allData.flatMap(d => [d.theirPrice, d.ourPrice]);
                    const minP = Math.min(...allPrices) * 0.98;
                    const maxP = Math.max(...allPrices) * 1.02;
                    const range = maxP - minP || 1;
                    const W = 700, H = 240, PAD = 40;
                    const colors = ['#165DFF', '#F53F3F', '#00B42A', '#FF7D00', '#722ED1'];

                    return (
                      <div style={{ overflowX: 'auto' }}>
                        <svg width={W} height={H} style={{ display: 'block', margin: '0 auto' }}>
                          {/* Y轴 */}
                          {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                            const y = PAD + (1 - ratio) * (H - PAD * 2);
                            const val = (minP + range * ratio).toFixed(0);
                            return (
                              <g key={ratio}>
                                <line x1={PAD} y1={y} x2={W - 20} y2={y} stroke="var(--border)" strokeDasharray="3,3" />
                                <text x={PAD - 4} y={y + 4} textAnchor="end" fontSize="10" fill="var(--text-3)">¥{val}</text>
                              </g>
                            );
                          })}
                          {/* 数据线 */}
                          {top5.map((comp, ci) => {
                            const hist = priceHistories[comp.id] || [];
                            if (hist.length < 2) return null;
                            const points = hist.map((d, i) => {
                              const x = PAD + (i / (hist.length - 1)) * (W - PAD - 20);
                              const y = PAD + (1 - (d.theirPrice - minP) / range) * (H - PAD * 2);
                              return `${x},${y}`;
                            }).join(' ');
                            return <polyline key={comp.id} points={points} fill="none" stroke={colors[ci]} strokeWidth="2" strokeLinejoin="round" />;
                          })}
                          {/* X轴标签 */}
                          {(priceHistories[top5[0]?.id] || []).filter((_, i) => i % 5 === 0).map((d, i, arr) => {
                            const idx = i * 5;
                            const x = PAD + (idx / ((priceHistories[top5[0]?.id] || []).length - 1)) * (W - PAD - 20);
                            return <text key={i} x={x} y={H - 8} textAnchor="middle" fontSize="10" fill="var(--text-3)">{d.date}</text>;
                          })}
                        </svg>
                        {/* 图例 */}
                        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 8 }}>
                          {top5.map((comp, ci) => (
                            <span key={comp.id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-2)' }}>
                              <span style={{ width: 12, height: 3, background: colors[ci], borderRadius: 2, display: 'inline-block' }} />
                              {comp.name.length > 6 ? comp.name.slice(0, 6) + '...' : comp.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
              {trendMetric === 'sales' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
                  {competitors.slice(0, 8).map(c => {
                    const ratio = c.ourSales / Math.max(c.theirSales, 1);
                    const barPct = Math.min(100, ratio * 100);
                    return (
                      <div key={c.id} style={{ padding: 12, background: 'var(--bg-2)', borderRadius: 8 }}>
                        <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-3)', marginBottom: 4 }}>
                          <span>我方 {c.ourSales?.toLocaleString()}</span>
                          <span>竞品 {c.theirSales.toLocaleString()}</span>
                        </div>
                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${barPct}%`, height: '100%', background: ratio >= 1 ? 'var(--success)' : '#FF7D00', borderRadius: 3 }} />
                        </div>
                        <div style={{ fontSize: 10, color: ratio >= 1 ? 'var(--success)' : '#FF7D00', marginTop: 2, textAlign: 'right' }}>
                          {ratio >= 1 ? '领先' : '落后'} {(ratio * 100).toFixed(0)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              {trendMetric === 'rating' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
                  {competitors.slice(0, 8).map(c => (
                    <div key={c.id} style={{ padding: 12, background: 'var(--bg-2)', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</div>
                      <div style={{ fontSize: 28, fontWeight: 700, color: '#FF7D00', marginBottom: 4 }}>★ {c.theirRating}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>竞品评分</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 市场格局 */}
          <div className="card">
            <div className="card-header"><span className="card-title">🗺️ 市场格局概览</span></div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                {platformStats.map(ps => {
                  const psItems = competitors.filter(c => c.platform === ps.key);
                  const avgOurPrice = (psItems.reduce((s, c) => s + c.ourPrice, 0) / psItems.length).toFixed(2);
                  const avgTheirPrice = (psItems.reduce((s, c) => s + c.theirPrice, 0) / psItems.length).toFixed(2);
                  return (
                    <div key={ps.key} style={{ padding: 16, border: '1px solid var(--border)', borderRadius: 8 }}>
                      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{ps.icon} {ps.name}</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                          <span style={{ color: 'var(--text-3)' }}>监控数</span><span style={{ fontWeight: 500 }}>{ps.count}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                          <span style={{ color: 'var(--text-3)' }}>我方均价</span><span style={{ fontWeight: 500 }}>¥{avgOurPrice}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                          <span style={{ color: 'var(--text-3)' }}>竞品均价</span><span style={{ fontWeight: 500 }}>¥{avgTheirPrice}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                          <span style={{ color: 'var(--text-3)' }}>优势率</span>
                          <span style={{ fontWeight: 500, color: parseFloat(ps.cheaperRate) > 50 ? 'var(--success)' : '#FF7D00' }}>{ps.cheaperRate}%</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Toast */}
      {toast && <div style={{ position: 'fixed', top: 80, right: 24, background: 'var(--success)', color: '#fff', padding: '10px 20px', borderRadius: 8, fontSize: 14, zIndex: 2000, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>✅ {toast}</div>}

      {/* 调价弹窗 */}
      {adjustItem && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setAdjustItem(null)}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 28, width: 440, boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 600 }}>调整价格</h3>
              <button onClick={() => setAdjustItem(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>✕</button>
            </div>
            <div style={{ padding: 12, background: 'var(--bg-2)', borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
              <div style={{ fontWeight: 500, marginBottom: 4 }}>{adjustItem.name}</div>
              <div>竞品价: <b>¥{adjustItem.theirPrice.toFixed(2)}</b> | 建议价: <b style={{ color: 'var(--primary)' }}>¥{(adjustItem.theirPrice * 0.95).toFixed(2)}</b></div>
            </div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>新价格 *</label>
            <input style={inputStyle} type="number" value={adjustPrice} onChange={e => setAdjustPrice(e.target.value)} placeholder="输入新价格" />
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>调价原因</label>
            <select style={inputStyle} value={adjustReason} onChange={e => setAdjustReason(e.target.value)}>
              <option value="">选择原因</option>
              <option value="跟随竞品">跟随竞品降价</option>
              <option value="促销活动">促销活动</option>
              <option value="成本变动">成本变动</option>
              <option value="库存清仓">库存清仓</option>
              <option value="其他">其他</option>
            </select>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-default" onClick={() => setAdjustItem(null)}>取消</button>
              <button className="btn btn-primary" onClick={handleAdjustPrice}>确认调价</button>
            </div>
          </div>
        </div>
      )}

      {/* 详情弹窗 */}
      {detailItem && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setDetailItem(null)}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 28, width: 560, maxHeight: '80vh', overflow: 'auto', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 600 }}>竞品详情</h3>
              <button onClick={() => setDetailItem(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>✕</button>
            </div>
            <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 16 }}>{detailItem.name}</div>
            {/* 价格走势预览 */}
            {priceHistories[detailItem.id] && (
              <div style={{ marginBottom: 16, padding: 12, background: 'var(--bg-2)', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 8 }}>30天价格走势</div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <MiniSparkline data={priceHistories[detailItem.id]} width={200} height={40} color="var(--primary)" secondColor="var(--danger)" />
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
                      <span style={{ color: 'var(--primary)', marginRight: 8 }}>━ 竞品价</span>
                      <span style={{ color: 'var(--danger)' }}>╌ 我方价</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {[
              ['竞品店铺', detailItem.competitor], ['平台', getPlatformInfo(detailItem.platform).icon + ' ' + getPlatformInfo(detailItem.platform).name],
              ['竞品价格', `¥${detailItem.theirPrice.toFixed(2)}`], ['我方价格', `¥${detailItem.ourPrice.toFixed(2)}`],
              ['价差', `${parseFloat(detailItem.priceDiff) > 0 ? '+' : ''}${detailItem.priceDiff}%`],
              ['竞品销量', detailItem.theirSales.toLocaleString()], ['我方销量', detailItem.ourSales?.toLocaleString() || '-'],
              ['竞品评分', `★ ${detailItem.theirRating}`], ['建议价格', `¥${(detailItem.theirPrice * 0.95).toFixed(2)}`],
              ['更新时间', detailItem.updatedAt?.slice(0, 19)],
            ].map(([label, value]) => (
              <div key={label} style={{ display: 'flex', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ width: 100, color: 'var(--text-3)' }}>{label}</span>
                <span style={{ fontWeight: label === '我方价格' || label === '竞品价格' ? 600 : 400 }}>{value}</span>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={() => { handleApplySuggestion(detailItem); setDetailItem(null); }}>应用建议价</button>
              <button className="btn btn-default" onClick={() => { setAdjustItem(detailItem); setAdjustPrice(detailItem.ourPrice.toString()); setDetailItem(null); }}>手动调价</button>
            </div>
          </div>
        </div>
      )}

      {/* 添加监控弹窗 */}
      {showAddMonitor && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowAddMonitor(false)}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 28, width: 480, boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 600 }}>添加竞品监控</h3>
              <button onClick={() => setShowAddMonitor(false)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>✕</button>
            </div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>商品名称 *</label>
            <input style={inputStyle} placeholder="输入商品名称" value={newMonitor.name} onChange={e => setNewMonitor(p => ({ ...p, name: e.target.value }))} />
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>竞品店铺</label>
            <input style={inputStyle} placeholder="竞品店铺名称" value={newMonitor.competitor} onChange={e => setNewMonitor(p => ({ ...p, competitor: e.target.value }))} />
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>平台 *</label>
            <select style={inputStyle} value={newMonitor.platform} onChange={e => setNewMonitor(p => ({ ...p, platform: e.target.value }))}>
              {PLATFORMS.map(p => <option key={p.key} value={p.key}>{p.icon} {p.name}</option>)}
            </select>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
              <div><label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>竞品价格 *</label><input style={inputStyle} type="number" placeholder="0.00" value={newMonitor.theirPrice} onChange={e => setNewMonitor(p => ({ ...p, theirPrice: e.target.value }))} /></div>
              <div><label style={{ display: 'block', marginBottom: 4, fontSize: 13 }}>我方价格 *</label><input style={inputStyle} type="number" placeholder="0.00" value={newMonitor.ourPrice} onChange={e => setNewMonitor(p => ({ ...p, ourPrice: e.target.value }))} /></div>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
              <button className="btn btn-default" onClick={() => setShowAddMonitor(false)}>取消</button>
              <button className="btn btn-primary" onClick={handleAddMonitor}>确认添加</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
