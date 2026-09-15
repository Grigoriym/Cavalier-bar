using System.Text;

namespace NickvisionCavalier.GNOME.Helpers;

/// <summary>
/// A Gtk.TemplateLoader that reads an embedded .ui resource and replaces all translatable strings
/// with the localized version, same as Builder.FromFile, before handing it to GTK's composite
/// template machinery
/// </summary>
public class TranslatedTemplateLoader : Gtk.TemplateLoader
{
    public static GLib.Bytes Load(string resourceName)
    {
        var xml = Builder.ReadTranslatedXml(resourceName);
        return GLib.Bytes.New(Encoding.UTF8.GetBytes(xml));
    }
}
