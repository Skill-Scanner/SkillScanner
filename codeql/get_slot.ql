/**
 * @name Empty block
 * @kind problem
 * @problem.severity warning
 * @id javascript/example/empty-block
 */

import javascript

from Token slot
where
slot.toString() = "getSlotValue"
and
slot.getPreviousToken().toString() = "."
and
slot.getPreviousToken().getPreviousToken().toString() = "Alexa"
//and
//slot.getPreviousToken().getPreviousToken().getPreviousToken().toString() = "."
select slot, "$@", slot, slot.toString()
