import { publicSiteUrl } from "@/lib/brand";
export const metadata = { alternates: { canonical: publicSiteUrl().href } };
import Landing from "@/components/landing/HomePage";
export default function HomePage() {
  return <Landing />;
}
