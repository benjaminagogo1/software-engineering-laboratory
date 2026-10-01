import { reports } from '../../api/endpoints'
import { ErrorNote } from '../../components/ErrorNote'
import { Loading } from '../../components/Loading'
import { useApi } from '../../lib/useApi'

/**
 * The monthly spending chart.
 *
 * The chart is rendered by the *server* — the same app/reports/monthly_chart.py
 * that the CLI's `chart` command writes to a file — and injected here as a
 * stylesheet plus a body fragment. Reimplementing it in JavaScript would mean
 * two renderers that drift, and the twenty-odd checks in tests/test_reports.py
 * would then be covering a chart nobody looks at.
 *
 * `dangerouslySetInnerHTML` is the right call here for a specific, checkable
 * reason rather than by habit: every user-supplied string in that renderer goes
 * through html.escape, so the values arriving are escaped by construction — not
 * by anything in this file. tests/test_reports.py pins that, and
 * tests/test_api.py pins that the fragment is exactly the markup the
 * standalone report carries.
 *
 * The cost, stated plainly: the in-page chart keeps the renderer's hover
 * tooltips rather than gaining richer cross-filtering. That is the trade for
 * having one implementation; if month-over-month overlays are wanted later,
 * that is when a second renderer earns its keep.
 *
 * @param {{month: string}} props
 */
export function MonthlyChart({ month }) {
  const { status, data, error } = useApi(
    () => reports.monthFragment(month),
    [month],
  )

  if (status === 'loading') {
    return <Loading label="Drawing the chart…" />
  }

  if (status === 'error') {
    return <ErrorNote error={error} />
  }

  return (
    <>
      {/* React renders a <style> element's children as text, so the rules have
          to go in through the same door as the markup. */}
      <style dangerouslySetInnerHTML={{ __html: data.css }} />
      <div
        className="spending-chart chart-host"
        dangerouslySetInnerHTML={{ __html: data.html }}
      />
    </>
  )
}
