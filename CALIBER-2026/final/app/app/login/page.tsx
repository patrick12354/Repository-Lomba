import { Suspense } from "react";
import { LoginForm } from "@/components/login-form";
import { titled } from "@/lib/i18n-server";

export const generateMetadata = titled("Sign in", "Masuk");

export default function Page() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
