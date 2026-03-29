"use client";

import { usePathname } from "next/navigation";
import Navbar from "./Navbar";

export default function NavbarWrapper() {
  const pathname = usePathname();

  // hide navbar on auth pages
  if (pathname.startsWith("/auth")) {
    return null;
  }

  return <Navbar />;
}