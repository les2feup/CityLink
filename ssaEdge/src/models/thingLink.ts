import {
  AnyUri,
  BaseLinkElement,
  LinkElement,
  ThingDescription,
} from "../../deps.ts";

export type ThingLinkLinkElement = BaseLinkElement & {
  rel: "describedby";
  type: "application/td+json";
  [k: string]: unknown;
};

export type PartialTD = Omit<
  ThingDescription,
  "@context" | "@type" | "links"
>;

export type ThingLink = PartialTD & {
  "@context": [
    "https://www.w3.org/2022/wot/td/v1.1",
    "https://www.w3.org/2022/wot/discovery",
    ...AnyUri[],
  ];
  "@type": "ThingLink";
  links: [ThingLinkLinkElement, ...LinkElement[]];
};

export function createThingLink(
  tdhref: AnyUri,
  extraContext: AnyUri[] = [],
  extraLinks: LinkElement[] = [],
  extraProps: PartialTD = {},
): ThingLink {
  return {
    "@context": [
      "https://www.w3.org/2022/wot/td/v1.1",
      "https://www.w3.org/2022/wot/discovery",
      ...extraContext,
    ],
    "@type": "ThingLink",
    links: [{
      rel: "describedby",
      href: tdhref,
      type: "application/td+json",
    }, ...extraLinks],
    ...extraProps,
  };
}
