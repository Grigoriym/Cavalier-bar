using NickvisionCavalier.GNOME.Helpers;
using static Nickvision.Aura.Localization.Gettext;

namespace NickvisionCavalier.GNOME.Controls;

/// <summary>
/// A dialog to show command-line help
/// </summary>
[GObject.Subclass<Adw.Window>(qualifiedName: nameof(CommandHelpDialog))]
[Gtk.Template<TranslatedTemplateLoader>("command_help_dialog.ui")]
public partial class CommandHelpDialog
{
    [Gtk.Connect] private Gtk.Label _helpLabel;

    private void Setup(Gtk.Window parent, string iconName, string help)
    {
        SetIconName(iconName);
        SetTransientFor(parent);
        _helpLabel.SetLabel(help);
    }

    /// <summary>
    /// Constructs a CommandHelpDialog
    /// </summary>
    /// <param name="parent">Gtk.Window</param>
    /// <param name="iconName">Icon name for the window</param>
    /// <param name="help">Help text</param>
    public static CommandHelpDialog Create(Gtk.Window parent, string iconName, string help)
    {
        var dialog = NewWithProperties([]);
        dialog.Setup(parent, iconName, help);
        return dialog;
    }
}
