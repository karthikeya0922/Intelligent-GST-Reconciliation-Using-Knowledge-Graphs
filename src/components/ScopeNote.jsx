import { Layers } from 'lucide-react';
import { useData } from '../context/DataContext';

/**
 * Explains which dataset the surrounding page is reading from.
 *
 * The platform holds two datasets that never join: the MongoDB-backed
 * operational scope (the filing entity's own trading counterparties, used by
 * reconciliation, compliance and the graph) and the research benchmark behind
 * the Dashboard and Vendor Risk Directory. Their vendor IDs use different
 * schemes entirely (V001 vs V-PUB-0001), so they cannot be reconciled.
 *
 * Without this note the two vendor counts read as a bug rather than as two
 * deliberate scopes.
 */
export default function ScopeNote({ benchmarkVendors = 2015 }) {
  const { vendors } = useData();
  const count = vendors?.length ?? 0;

  return (
    <div className="scope-note" role="note">
      <Layers size={14} className="scope-note-icon" />
      <span>
        <strong>Operational scope:</strong> the filing entity&rsquo;s{' '}
        {count > 0 ? count : ''} trading counterparties and their invoices, read
        from MongoDB. This is a separate, deliberately smaller dataset than the{' '}
        {benchmarkVendors.toLocaleString('en-IN')}-vendor research benchmark
        behind the Dashboard and Vendor Risk Directory.
      </span>
    </div>
  );
}
