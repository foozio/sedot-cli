class Sedot < Formula
  include Language::Python::Virtualenv

  desc "CLI video scraper for Instagram posts/reels and Threads"
  homepage "https://github.com/foozio/sedot-cli"
  url "https://github.com/foozio/sedot-cli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "calculate_this_from_tarball"
  license "MIT"  # Assuming, check actual license

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/sedot", "--help"
  end
end