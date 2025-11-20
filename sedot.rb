class Sedot < Formula
  include Language::Python::Virtualenv

  desc "CLI video scraper for Instagram posts/reels and Threads"
  homepage "https://github.com/foozio/homebrew-sedot-cli"
  url "https://github.com/foozio/homebrew-sedot-cli/archive/refs/tags/v0.1.1.tar.gz"
  sha256 "3259a4974d44c5c636af8811814bca507de5ec8d4157dc5d544997e1c827fef4"
  license "MIT"

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/sedot", "--help"
  end
end