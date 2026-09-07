import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  FileSearch,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  Minus
} from 'lucide-react';
import { getVendors } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

export default function VendorRiskTable() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // State initialized from URL query params or defaults
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [riskClass, setRiskClass] = useState(searchParams.get('risk_class') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || '');
  const [sort, setSort] = useState(searchParams.get('sort') || 'risk_score');
  const [order, setOrder] = useState(searchParams.get('order') || 'desc');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));
  const [pageSize, setPageSize] = useState(parseInt(searchParams.get('page_size') || '20', 10));

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadVendors = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getVendors({
        search: search.trim() || undefined,
        risk_class: riskClass || undefined,
        priority: priority || undefined,
        sort,
        order,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load vendors:', err);
      setError(err.message || 'Unable to retrieve vendors from server.');
    } finally {
      setLoading(false);
    }
  };

  // Sync state changes with URL and fetch
  useEffect(() => {
    const params = {};
    if (search) params.search = search;
    if (riskClass) params.risk_class = riskClass;
    if (priority) params.priority = priority;
    if (sort) params.sort = sort;
    if (order) params.order = order;
    if (page > 1) params.page = page.toString();
    if (pageSize !== 20) params.page_size = pageSize.toString();
    setSearchParams(params, { replace: true });

    loadVendors();
  }, [search, riskClass, priority, sort, order, page, pageSize]);

  const handleSort = (col) => {
    if (sort === col) {
      setOrder(order === 'asc' ? 'desc' : 'asc');
    } else {
      setSort(col);
      setOrder('desc');
    }
    setPage(1);
  };

  const getSortIcon = (col) => {
    if (sort !== col) return <ArrowUpDown size={12} className="text-muted" />;
    return order === 'asc' ? <ArrowUp size={12} className="text-accent" /> : <ArrowDown size={12} className="text-accent" />;
  };

  const renderTrendIcon = (trend) => {
    switch (trend) {
      case 'deteriorating':
        return <span className="text-danger flex items-center gap-1"><TrendingUp size={14} /> Deteriorating</span>;
      case 'improving':
        return <span className="text-success flex items-center gap-1"><TrendingDown size={14} /> Improving</span>;
      case 'volatile':
        return <span className="text-warning flex items-center gap-1"><Activity size={14} /> Volatile</span>;
      default:
        return <span className="text-muted flex items-center gap-1"><Minus size={14} /> Stable</span>;
    }
  };

  return (
    <div className="vendors-page">
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>🏢 Vendor Risk Directory</h2>
            <p>Tabular XGBoost ML Risk Indicator Scores & Financial ITC Exposure Portfolio</p>
          </div>
          <button className="btn-outline flex items-center gap-1" onClick={loadVendors}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </div>

      <ResearchDisclaimer compact />

      {/* Filter and Search Bar */}
      <div className="filter-bar">
        <div className="flex items-center gap-1 flex-1">
          <Search size={16} className="text-muted" />
          <input
            type="text"
            className="filter-input"
            placeholder="Search by vendor ID, name, GSTIN, or state..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={15} className="text-muted" />
          <select
            className="filter-select"
            value={riskClass}
            onChange={(e) => {
              setRiskClass(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Risk Classes</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
          </select>

          <select
            className="filter-select"
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Operational Priorities</option>
            <option value="CRITICAL">Critical Priority</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>

          <select
            className="filter-select"
            value={pageSize}
            onChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(1);
            }}
          >
            <option value={10}>10 / page</option>
            <option value={20}>20 / page</option>
            <option value={50}>50 / page</option>
            <option value={100}>100 / page</option>
          </select>
        </div>
      </div>

      {/* Data Table Container */}
      <div className="card">
        {loading ? (
          <div className="state-container state-loading">
            <div className="spinner" />
            <p>Loading vendor risk records...</p>
          </div>
        ) : error ? (
          <div className="state-container state-error">
            <AlertCircle size={36} className="error-icon" />
            <p className="text-muted">{error}</p>
            <button className="btn-primary mt-2" onClick={loadVendors}>Retry</button>
          </div>
        ) : !data?.items || data.items.length === 0 ? (
          <div className="state-container state-empty">
            <AlertCircle size={36} className="empty-icon" />
            <h4>No Vendors Matched Criteria</h4>
            <p className="text-muted">Try clearing the search query or adjusting risk/priority filters.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort('vendor_id')} className="cursor-pointer">
                    <div className="flex items-center gap-1">Vendor {getSortIcon('vendor_id')}</div>
                  </th>
                  <th onClick={() => handleSort('risk_class')} className="cursor-pointer">
                    <div className="flex items-center gap-1">Risk Band {getSortIcon('risk_class')}</div>
                  </th>
                  <th onClick={() => handleSort('risk_score')} className="cursor-pointer">
                    <div className="flex items-center gap-1">0–100 ML Score {getSortIcon('risk_score')}</div>
                  </th>
                  <th onClick={() => handleSort('itc_exposure')} className="cursor-pointer">
                    <div className="flex items-center gap-1">ITC Exposure {getSortIcon('itc_exposure')}</div>
                  </th>
                  <th onClick={() => handleSort('priority')} className="cursor-pointer">
                    <div className="flex items-center gap-1">Operational Priority {getSortIcon('priority')}</div>
                  </th>
                  <th>Trend</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((v) => (
                  <tr key={v.vendor_id} className="hover-row">
                    <td>
                      <div className="font-semibold text-primary">{v.vendor_name}</div>
                      <div className="text-xs text-muted">
                        <span className="badge-tag">{v.vendor_id}</span> • {v.gstin} • {v.state}
                      </div>
                    </td>

                    <td>
                      <span className={`badge-${v.risk_band.toLowerCase()}`}>
                        {v.risk_band}
                      </span>
                    </td>

                    <td>
                      <div className="flex items-center gap-2">
                        <div className="progress-bar-bg" style={{ width: '60px', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(v.risk_score, 100)}%`,
                              height: '100%',
                              backgroundColor: v.risk_score > 66 ? '#ef4444' : v.risk_score > 33 ? '#f59e0b' : '#22c55e',
                            }}
                          />
                        </div>
                        <span className="font-mono text-sm font-bold">{v.risk_score.toFixed(1)}</span>
                      </div>
                    </td>

                    <td>
                      <div className="font-semibold">{formatINR(v.itc_exposure)}</div>
                      <div className="text-xs text-muted">{v.invoice_count} invoices</div>
                    </td>

                    <td>
                      <span className={`badge-${v.priority.toLowerCase()}`}>
                        {v.priority}
                      </span>
                    </td>

                    <td className="text-xs">
                      {renderTrendIcon(v.trend)}
                    </td>

                    <td className="text-right">
                      <div className="flex justify-end gap-1">
                        <button
                          className="btn-sm btn-outline flex items-center gap-1"
                          onClick={() => navigate(`/vendors/${v.vendor_id}`)}
                          title="View complete risk breakdown"
                        >
                          <Eye size={12} /> Detail
                        </button>
                        <button
                          className="btn-sm btn-primary flex items-center gap-1"
                          onClick={() => navigate(`/investigation/${v.vendor_id}`)}
                          title="Open 7-step investigation workspace"
                        >
                          <FileSearch size={12} /> Investigate
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            <div className="pagination-controls px-3">
              <div>
                Showing <strong>{((page - 1) * pageSize) + 1}</strong> to{' '}
                <strong>{Math.min(page * pageSize, data.pagination.total_records)}</strong> of{' '}
                <strong>{data.pagination.total_records.toLocaleString()}</strong> vendors
              </div>
              <div className="flex gap-1 items-center">
                <button
                  className="btn-page"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <span className="px-2 text-xs">
                  Page <strong>{page}</strong> of <strong>{data.pagination.total_pages}</strong>
                </span>
                <button
                  className="btn-page"
                  disabled={page >= data.pagination.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
