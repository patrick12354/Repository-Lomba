import { Suspense } from "react";
import { taskCounts } from "@/lib/data";
import { TodoBoard } from "@/components/todo-board";
import { DecideSteps } from "@/components/decide-steps";
import { getLang, titled } from "@/lib/i18n-server";

export const generateMetadata = titled("To do", "Tugas");

export default function Page() {
  return (
    <Suspense>
      <Board />
    </Suspense>
  );
}

async function Board() {
  await getLang();
  return (
    <div className="space-y-3">
      <DecideSteps current="act" />
      <TodoBoard counts={taskCounts()} />
    </div>
  );
}
