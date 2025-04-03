import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import { redirect } from "next/navigation"

export function SidebarOptInForm() {
  return (
    <Card className="gap-2 py-4 shadow-none">
      <CardContent className="px-4">
        <form>
          <div className="grid gap-2.5">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                localStorage.removeItem("token")
                localStorage.removeItem("role")
                redirect("/")
              }}
            >
              Logout
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
