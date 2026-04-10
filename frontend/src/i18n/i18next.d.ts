import "i18next";

declare module "i18next" {
  interface CustomTypeOptions {
    defaultNS: "common";
    // Disable strict key checking to allow cross-namespace keys and dynamic keys
    allowObjectInHTMLChildren: true;
  }
}
