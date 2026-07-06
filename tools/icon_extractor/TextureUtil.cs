using System;
using System.Linq;
using CUE4Parse.FileProvider;
using CUE4Parse.UE4.Assets.Exports.Texture;
using CUE4Parse_Conversion.Textures;
using SkiaSharp;

// Shared texture-decode helper: cooked package -> 64x64 PNG bytes. Used by both
// the static pak-discovery path (ItemIconDiscovery.cs) and the legacy
// iconlist.txt stem-match path (Program.cs), so both modes produce byte-identical
// output for the same texture.
static class TextureUtil
{
    public static byte[] DecodePackageToPng64(DefaultFileProvider provider, string packageKey)
    {
        var pkg = provider.LoadPackage(packageKey);
        var tex = pkg.GetExports().OfType<UTexture2D>().FirstOrDefault();
        if (tex == null) return null;
        var ctex = tex.Decode(ETexturePlatform.DesktopMobile);
        if (ctex == null) return null;
        using var bmp = ctex.ToSkBitmap();
        if (bmp == null) return null;
        using var resized = bmp.Resize(new SKImageInfo(64, 64), SKFilterQuality.High) ?? bmp;
        using var img = SKImage.FromBitmap(resized);
        using var png = img.Encode(SKEncodedImageFormat.Png, 100);
        return png.ToArray();
    }
}
