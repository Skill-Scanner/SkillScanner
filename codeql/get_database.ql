/**
 * @name Empty block
 * @kind problem
 * @problem.severity warning
 * @id javascript/example/empty-block
 */

import javascript

from ControlFlowNode cfg, AnalyzedNode source
where
cfg.toString().toLowerCase().indexOf("dynamodb") > -1
select cfg, "$@", cfg, cfg.toString()