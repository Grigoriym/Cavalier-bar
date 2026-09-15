using System.IO;
using System.Reflection;
using System.Xml;
using static Nickvision.Aura.Localization.Gettext;

namespace NickvisionCavalier.GNOME.Helpers;

public static class Builder
{
    /// <summary>
    /// Reads an embedded .ui resource and replaces all translatable strings with the localized version
    /// </summary>
    /// <param name="name">The name of the embedded resource</param>
    /// <returns>The translated UI XML as a string</returns>
    public static string ReadTranslatedXml(string name)
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name);
        using var reader = new StreamReader(stream!);
        var uiContents = reader.ReadToEnd();
        var xml = new XmlDocument();
        xml.LoadXml(uiContents);
        var elements = xml.GetElementsByTagName("*");
        foreach (XmlElement element in elements)
        {
            if (element.HasAttribute("translatable"))
            {
                element.RemoveAttribute("translatable");
                if (element.HasAttribute("context"))
                {
                    var context = element.GetAttribute("context");
                    element.InnerText = _p(context, element.InnerText);
                }
                else
                {
                    element.InnerText = _(element.InnerText);
                }
            }
        }
        return xml.OuterXml;
    }

    /// <summary>
    /// Creates a Gtk.Builder from an embedded resource and replaces all translatable strings with the localized version
    /// </summary>
    /// <param name="name">The name of the embedded resource</param>
    /// <returns>Gtk.Builder</returns>
    public static Gtk.Builder FromFile(string name) => Gtk.Builder.NewFromString(ReadTranslatedXml(name), -1);
}
